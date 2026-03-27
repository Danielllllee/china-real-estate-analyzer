"""可比交易法估值模型

原理：基于同区域、同类型房产的近期真实成交价，
通过调整面积、楼层、装修、房龄等差异因素，
得出目标房产的合理市场价格。

这是最贴近市场的估值方法。
"""
import numpy as np
from utils.database import query_df
from utils.constants import (
    DECORATION_ADJUSTMENT, FLOOR_ADJUSTMENT,
    AGE_DEPRECIATION_RATE, ORIENTATION_ADJUSTMENT,
)


def get_comparable_transactions(
    city: str,
    district: str,
    community_id: int = None,
    months: int = 6,
    min_samples: int = 5,
) -> dict:
    """获取可比交易数据"""
    if community_id:
        # 先找同小区成交
        txns = query_df("""
            SELECT t.*, c.build_year, c.name as community_name
            FROM transactions t
            JOIN communities c ON t.community_id = c.id
            WHERE t.community_id = ?
            AND t.deal_date >= date('now', ?)
            ORDER BY t.deal_date DESC
        """, [community_id, f"-{months} months"])

        if len(txns) >= min_samples:
            return {"level": "community", "data": txns}

    # 同区域成交
    txns = query_df("""
        SELECT t.*, c.build_year, c.name as community_name
        FROM transactions t
        JOIN communities c ON t.community_id = c.id
        WHERE c.city = ? AND c.district = ?
        AND t.deal_date >= date('now', ?)
        ORDER BY t.deal_date DESC
    """, [city, district, f"-{months} months"])

    return {"level": "district", "data": txns}


def adjust_price(
    base_unit_price: float,
    target_floor: str = "mid",
    target_decoration: str = "fine",
    target_age: int = 10,
    target_orientation: str = "south",
    comp_floor: str = "mid",
    comp_decoration: str = "fine",
    comp_age: int = 10,
    comp_orientation: str = "south",
) -> float:
    """根据差异调整价格

    从可比物的实际价格出发，调整各项差异到目标条件
    """
    adjustment = 1.0

    # 楼层调整
    floor_diff = FLOOR_ADJUSTMENT.get(target_floor, 0) - FLOOR_ADJUSTMENT.get(comp_floor, 0)
    adjustment += floor_diff

    # 装修调整
    deco_diff = DECORATION_ADJUSTMENT.get(target_decoration, 0) - DECORATION_ADJUSTMENT.get(comp_decoration, 0)
    adjustment += deco_diff

    # 房龄调整
    age_diff = (comp_age - target_age) * AGE_DEPRECIATION_RATE  # 越新越贵
    adjustment += age_diff

    # 朝向调整
    orient_diff = ORIENTATION_ADJUSTMENT.get(target_orientation, 0) - ORIENTATION_ADJUSTMENT.get(comp_orientation, 0)
    adjustment += orient_diff

    return base_unit_price * adjustment


def estimate_by_comparable(
    city: str,
    district: str,
    target_area: float = 90,
    target_floor: str = "mid",
    target_decoration: str = "fine",
    target_age: int = 10,
    target_orientation: str = "south",
    community_id: int = None,
) -> dict:
    """可比交易法估值

    Args:
        city, district: 城市和区域
        target_*: 目标房产的各项特征
        community_id: 指定小区ID（可选）

    Returns:
        估值结果
    """
    result = get_comparable_transactions(city, district, community_id)
    txns = result["data"]

    if txns.empty:
        return {
            "model": "comparable",
            "model_name": "可比交易法",
            "error": "无可比交易数据",
        }

    current_year = 2025
    adjusted_prices = []

    for _, txn in txns.iterrows():
        comp_age = current_year - (txn["build_year"] if txn["build_year"] else current_year - 10)
        adj_price = adjust_price(
            txn["unit_price"],
            target_floor=target_floor,
            target_decoration=target_decoration,
            target_age=target_age,
            target_orientation=target_orientation,
            comp_floor=txn["floor_level"] or "mid",
            comp_decoration=txn["decoration"] or "fine",
            comp_age=comp_age,
            comp_orientation=txn["orientation"] or "south",
        )
        adjusted_prices.append(adj_price)

    prices = np.array(adjusted_prices)

    # 去除异常值（IQR法）
    q1, q3 = np.percentile(prices, [25, 75])
    iqr = q3 - q1
    mask = (prices >= q1 - 1.5 * iqr) & (prices <= q3 + 1.5 * iqr)
    clean_prices = prices[mask]

    if len(clean_prices) < 3:
        clean_prices = prices

    return {
        "model": "comparable",
        "model_name": "可比交易法",
        "fair_value_per_sqm": round(np.mean(clean_prices)),
        "conservative_value": round(np.percentile(clean_prices, 25)),
        "optimistic_value": round(np.percentile(clean_prices, 75)),
        "median_value": round(np.median(clean_prices)),
        "std_dev": round(np.std(clean_prices)),
        "sample_count": len(clean_prices),
        "total_samples": len(prices),
        "comparison_level": result["level"],
        "price_range": [round(clean_prices.min()), round(clean_prices.max())],
    }
