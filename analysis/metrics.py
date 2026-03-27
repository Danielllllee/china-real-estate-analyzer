"""核心分析指标计算 — 仅基于真实数据"""
import pandas as pd
from core.database import query_df


def get_city_overview(city: str) -> dict:
    """获取城市概览数据（仅均价）"""
    latest_month = query_df("""
        SELECT MAX(month) as m FROM district_stats WHERE city = ?
    """, [city]).iloc[0]["m"]

    districts = query_df("""
        SELECT district, avg_unit_price
        FROM district_stats
        WHERE city = ? AND month = ?
        ORDER BY avg_unit_price DESC
    """, [city, latest_month])

    return {
        "city": city,
        "latest_month": latest_month,
        "districts": districts,
    }


def get_district_detail(city: str, district: str) -> dict:
    """获取区域详细数据"""
    latest = query_df("""
        SELECT avg_unit_price FROM district_stats
        WHERE city = ? AND district = ?
        ORDER BY month DESC LIMIT 1
    """, [city, district])

    return {
        "city": city,
        "district": district,
        "latest_price": latest.iloc[0]["avg_unit_price"] if not latest.empty else None,
    }
