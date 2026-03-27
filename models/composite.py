"""综合估值模型

将四个独立估值模型的结果加权融合，
给出最终的估值区间和投资建议。
"""
import yaml
import os
from models.rental_yield import (
    get_area_rental_data, get_community_rental_data,
    estimate_by_rental_yield, evaluate_current_price,
)
from models.comparable import estimate_by_comparable
from models.dcf import calculate_dcf
from models.cost_approach import get_land_cost, estimate_by_cost


def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def composite_valuation(
    city: str,
    district: str,
    area: float = 90,
    floor_level: str = "mid",
    decoration: str = "fine",
    building_age: int = 10,
    orientation: str = "south",
    community_id: int = None,
    current_price_per_sqm: float = None,
    weights: dict = None,
) -> dict:
    """综合估值

    Args:
        city, district: 城市和区域
        area: 面积
        floor_level, decoration, building_age, orientation: 房产特征
        community_id: 指定小区（可选）
        current_price_per_sqm: 当前市场价（用于评估偏离度）
        weights: 自定义权重

    Returns:
        综合估值结果
    """
    config = load_config()
    val_config = config["valuation"]

    if weights is None:
        weights = {
            "rental_yield": 0.30,
            "comparable": 0.40,
            "dcf": 0.20,
            "cost_approach": 0.10,
        }

    results = {}
    errors = []

    # 1. 租金收益率法
    rental_data = None
    if community_id:
        rental_data = get_community_rental_data(community_id)
    if not rental_data:
        rental_data = get_area_rental_data(city, district)

    if rental_data:
        annual_rent = rental_data["avg_rent_per_sqm"] * 12
        results["rental_yield"] = estimate_by_rental_yield(
            annual_rent,
            risk_free_rate=val_config["risk_free_rate"],
            risk_premium=val_config["property_risk_premium"],
        )
    else:
        errors.append("租金收益率法：无租金数据")

    # 2. 可比交易法
    comp_result = estimate_by_comparable(
        city, district,
        target_area=area,
        target_floor=floor_level,
        target_decoration=decoration,
        target_age=building_age,
        target_orientation=orientation,
        community_id=community_id,
    )
    if "error" not in comp_result:
        results["comparable"] = comp_result
    else:
        errors.append(f"可比交易法：{comp_result['error']}")

    # 3. DCF
    if rental_data:
        monthly_rent_psm = rental_data["avg_rent_per_sqm"]
        dcf_config = val_config["dcf"]
        remaining_years = max(70 - building_age, 20)

        results["dcf"] = calculate_dcf(
            monthly_rent_per_sqm=monthly_rent_psm,
            area=area,
            discount_rate=val_config["risk_free_rate"] + val_config["property_risk_premium"],
            rent_growth_rate=dcf_config["rent_growth_rate"],
            projection_years=dcf_config["projection_years"],
            terminal_cap_rate=dcf_config["terminal_cap_rate"],
            remaining_years=remaining_years,
        )
    else:
        errors.append("DCF：无租金数据")

    # 4. 成本法
    land_data = get_land_cost(city, district)
    if land_data:
        cost_config = val_config["cost"]
        avg_construction = sum(cost_config["construction_cost_per_sqm"]) / 2
        results["cost_approach"] = estimate_by_cost(
            land_floor_price=land_data["avg_floor_price"],
            construction_cost=avg_construction,
            developer_margin=cost_config["developer_margin"],
        )
    else:
        errors.append("成本法：无土地数据")

    # 加权综合
    total_weight = 0
    weighted_fair = 0
    weighted_conservative = 0
    weighted_optimistic = 0

    for model_key, result in results.items():
        w = weights.get(model_key, 0)
        if "fair_value_per_sqm" in result:
            weighted_fair += result["fair_value_per_sqm"] * w
            weighted_conservative += result["conservative_value"] * w
            weighted_optimistic += result["optimistic_value"] * w
            total_weight += w

    if total_weight > 0:
        # 重新归一化权重
        composite_fair = weighted_fair / total_weight
        composite_conservative = weighted_conservative / total_weight
        composite_optimistic = weighted_optimistic / total_weight
    else:
        return {"error": "所有估值模型均无数据", "errors": errors}

    output = {
        "composite": {
            "fair_value_per_sqm": round(composite_fair),
            "conservative_value": round(composite_conservative),
            "optimistic_value": round(composite_optimistic),
            "fair_total_price": round(composite_fair * area / 10000, 1),
            "conservative_total_price": round(composite_conservative * area / 10000, 1),
            "optimistic_total_price": round(composite_optimistic * area / 10000, 1),
        },
        "models": results,
        "weights_used": {k: weights.get(k, 0) for k in results},
        "effective_weight": total_weight,
        "errors": errors,
        "params": {
            "city": city,
            "district": district,
            "area": area,
            "floor_level": floor_level,
            "decoration": decoration,
            "building_age": building_age,
        },
    }

    # 如果有当前价格，进行偏离度评估
    if current_price_per_sqm and "rental_yield" in results:
        output["price_assessment"] = evaluate_current_price(
            current_price_per_sqm, results["rental_yield"]
        )
        fair = output["composite"]["fair_value_per_sqm"]
        dev = (current_price_per_sqm - fair) / fair
        output["composite_assessment"] = {
            "current_price": current_price_per_sqm,
            "composite_fair_value": fair,
            "deviation": round(dev, 4),
            "deviation_pct": f"{dev*100:+.1f}%",
            "recommendation": _get_recommendation(dev),
        }

    return output


def _get_recommendation(deviation: float) -> str:
    if deviation < -0.20:
        return "强烈推荐买入 - 价格显著低于内在价值"
    elif deviation < -0.10:
        return "推荐买入 - 价格低于合理估值"
    elif deviation < -0.05:
        return "可以考虑 - 价格略低于估值"
    elif deviation < 0.05:
        return "合理定价 - 视个人需求决定"
    elif deviation < 0.15:
        return "偏贵 - 建议等待或议价"
    elif deviation < 0.30:
        return "明显高估 - 不建议此时买入"
    else:
        return "严重高估 - 强烈不建议买入"
