"""成本法估值模型

第一性原理：房产的价值不应长期低于其重置成本。
重置成本 = 土地成本 + 建造成本 + 合理利润 + 税费

如果市场价低于重置成本，要么说明：
1. 存在安全边际（适合买入）
2. 土地价格虚高，开发商不可持续

如果市场价远高于重置成本，说明存在投机溢价。
"""
import numpy as np
from core.database import query_df


def get_land_cost(city: str, district: str, recent_years: int = 3) -> dict:
    """获取区域近期土地楼面价"""
    lands = query_df("""
        SELECT floor_price, sale_date
        FROM land_sales
        WHERE city = ? AND district = ?
        AND sale_date >= date('now', ?)
        ORDER BY sale_date DESC
    """, [city, district, f"-{recent_years} years"])

    if lands.empty:
        return None

    return {
        "avg_floor_price": lands["floor_price"].mean(),
        "median_floor_price": lands["floor_price"].median(),
        "latest_floor_price": lands.iloc[0]["floor_price"],
        "sample_count": len(lands),
    }


def estimate_by_cost(
    land_floor_price: float,
    construction_cost: float = 3500,
    developer_margin: float = 0.12,
    tax_and_fee_rate: float = 0.08,
    marketing_cost_rate: float = 0.03,
    finance_cost_rate: float = 0.05,
) -> dict:
    """成本法估值

    Args:
        land_floor_price: 土地楼面价（元/㎡）
        construction_cost: 建造成本（元/㎡）
        developer_margin: 开发商利润率
        tax_and_fee_rate: 税费比例
        marketing_cost_rate: 营销费用比例
        finance_cost_rate: 财务费用比例（占总投资）

    Returns:
        估值结果
    """
    # 硬成本
    hard_cost = land_floor_price + construction_cost

    # 软成本
    soft_cost = hard_cost * (tax_and_fee_rate + marketing_cost_rate + finance_cost_rate)

    # 总成本
    total_cost = hard_cost + soft_cost

    # 含利润的合理售价
    fair_value = total_cost * (1 + developer_margin)

    # 三档估值
    # 保守：低建造成本、低利润
    conservative = (land_floor_price + construction_cost * 0.85) * (1 + tax_and_fee_rate + marketing_cost_rate + finance_cost_rate) * (1 + 0.08)
    # 乐观：高建造成本、高利润
    optimistic = (land_floor_price + construction_cost * 1.15) * (1 + tax_and_fee_rate + marketing_cost_rate + finance_cost_rate) * (1 + 0.18)

    return {
        "model": "cost_approach",
        "model_name": "成本法",
        "fair_value_per_sqm": round(fair_value),
        "conservative_value": round(conservative),
        "optimistic_value": round(optimistic),
        "land_cost": round(land_floor_price),
        "construction_cost": round(construction_cost),
        "soft_cost": round(soft_cost),
        "total_cost": round(total_cost),
        "developer_margin": developer_margin,
        "cost_breakdown": {
            "土地成本": round(land_floor_price),
            "建造成本": round(construction_cost),
            "税费": round(hard_cost * tax_and_fee_rate),
            "营销费用": round(hard_cost * marketing_cost_rate),
            "财务费用": round(hard_cost * finance_cost_rate),
            "开发商利润": round(total_cost * developer_margin),
        },
    }
