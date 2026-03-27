"""租金收益率估值模型

第一性原理：房产是一个产生现金流（租金）的资产。
其合理价格 = 年租金 / 合理资本化率。
合理资本化率 = 无风险利率 + 房产风险溢价。

如果实际价格远高于该估值，说明房价存在泡沫；
如果低于该估值，说明有安全边际。
"""
import numpy as np
from core.database import query_df


def get_area_rental_data(city: str, district: str) -> dict:
    """获取区域租金数据（基于district_stats）"""
    stats = query_df("""
        SELECT avg_rent_per_sqm FROM district_stats
        WHERE city = ? AND district = ?
        ORDER BY month DESC LIMIT 1
    """, [city, district])

    if stats.empty or stats.iloc[0]["avg_rent_per_sqm"] is None:
        return None

    avg_rent = stats.iloc[0]["avg_rent_per_sqm"]
    return {
        "avg_rent_per_sqm": avg_rent,
        "median_rent_per_sqm": avg_rent,
        "rent_p25": avg_rent * 0.85,
        "rent_p75": avg_rent * 1.15,
        "sample_count": 1,
    }


def get_community_rental_data(community_id: int) -> dict:
    """获取小区级别租金数据（暂无真实数据）"""
    return None


def estimate_by_rental_yield(
    annual_rent_per_sqm: float,
    risk_free_rate: float = 0.025,
    risk_premium: float = 0.025,
    vacancy_rate: float = 0.05,
    maintenance_ratio: float = 0.005,
) -> dict:
    """基于租金收益率估算合理房价

    Args:
        annual_rent_per_sqm: 年租金（元/㎡）
        risk_free_rate: 无风险利率（10年期国债）
        risk_premium: 房产风险溢价
        vacancy_rate: 空置率
        maintenance_ratio: 年维护费率（占房价比例，迭代求解时使用近似值）

    Returns:
        估值结果字典
    """
    # 合理资本化率（cap rate）
    cap_rate = risk_free_rate + risk_premium

    # 净租金 = 毛租金 × (1 - 空置率) - 维护费（简化处理）
    net_rent = annual_rent_per_sqm * (1 - vacancy_rate)

    # 保守/中性/乐观三档
    # 保守：使用较高的cap rate（6%）
    # 中性：使用计算的cap rate
    # 乐观：使用较低的cap rate（4%）
    conservative_cap = max(cap_rate, 0.06)
    optimistic_cap = min(cap_rate, 0.04)

    fair_value = net_rent / cap_rate
    conservative_value = net_rent / conservative_cap
    optimistic_value = net_rent / optimistic_cap

    return {
        "model": "rental_yield",
        "model_name": "租金收益率法",
        "fair_value_per_sqm": round(fair_value),
        "conservative_value": round(conservative_value),
        "optimistic_value": round(optimistic_value),
        "cap_rate": round(cap_rate, 4),
        "net_annual_rent_per_sqm": round(net_rent, 1),
        "gross_annual_rent_per_sqm": round(annual_rent_per_sqm, 1),
        "vacancy_rate": vacancy_rate,
        "risk_free_rate": risk_free_rate,
        "risk_premium": risk_premium,
    }


def evaluate_current_price(current_price_per_sqm: float, valuation: dict) -> dict:
    """评估当前价格相对于估值的偏离度"""
    fair = valuation["fair_value_per_sqm"]
    deviation = (current_price_per_sqm - fair) / fair

    # 实际租金收益率
    actual_yield = valuation["net_annual_rent_per_sqm"] / current_price_per_sqm if current_price_per_sqm > 0 else 0

    if deviation > 0.3:
        assessment = "严重高估"
    elif deviation > 0.15:
        assessment = "明显高估"
    elif deviation > 0.05:
        assessment = "轻微高估"
    elif deviation > -0.05:
        assessment = "合理"
    elif deviation > -0.15:
        assessment = "轻微低估"
    else:
        assessment = "明显低估"

    return {
        "current_price": current_price_per_sqm,
        "fair_value": fair,
        "deviation": round(deviation, 4),
        "deviation_pct": f"{deviation*100:+.1f}%",
        "actual_yield": round(actual_yield, 4),
        "actual_yield_pct": f"{actual_yield*100:.2f}%",
        "assessment": assessment,
    }
