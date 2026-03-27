"""核心分析指标计算"""
import pandas as pd
import numpy as np
from core.database import query_df


def get_city_overview(city: str) -> dict:
    """获取城市概览数据"""
    # 最新月份各区域统计
    latest_month = query_df("""
        SELECT MAX(month) as m FROM district_stats WHERE city = ?
    """, [city]).iloc[0]["m"]

    districts = query_df("""
        SELECT district, avg_unit_price, median_unit_price,
               transaction_count, avg_rent_per_sqm, rent_to_price_ratio,
               listing_count, avg_deal_cycle
        FROM district_stats
        WHERE city = ? AND month = ?
        ORDER BY avg_unit_price DESC
    """, [city, latest_month])

    # 历史趋势（按月）
    trend = query_df("""
        SELECT month,
               AVG(avg_unit_price) as city_avg_price,
               AVG(avg_rent_per_sqm) as city_avg_rent,
               SUM(transaction_count) as city_txn_count,
               AVG(rent_to_price_ratio) as city_rtp
        FROM district_stats
        WHERE city = ?
        GROUP BY month
        ORDER BY month
    """, [city])

    return {
        "city": city,
        "latest_month": latest_month,
        "districts": districts,
        "trend": trend,
    }


def get_district_detail(city: str, district: str) -> dict:
    """获取区域详细数据"""
    # 小区列表
    communities = query_df("""
        SELECT c.id, c.name, c.build_year, c.total_units, c.property_fee,
               AVG(l.unit_price) as avg_listing_price,
               COUNT(l.id) as listing_count
        FROM communities c
        LEFT JOIN listings l ON c.id = l.community_id
        WHERE c.city = ? AND c.district = ?
        GROUP BY c.id
        ORDER BY avg_listing_price DESC
    """, [city, district])

    # 成交分布
    txn_distribution = query_df("""
        SELECT t.unit_price, t.area, t.deal_date, c.name as community_name
        FROM transactions t
        JOIN communities c ON t.community_id = c.id
        WHERE c.city = ? AND c.district = ?
        AND t.deal_date >= date('now', '-6 months')
        ORDER BY t.deal_date DESC
    """, [city, district])

    # 租金分布
    rent_distribution = query_df("""
        SELECT r.rent_per_sqm, r.area, c.name as community_name
        FROM rentals r
        JOIN communities c ON r.community_id = c.id
        WHERE c.city = ? AND c.district = ?
    """, [city, district])

    # 价格趋势
    price_trend = query_df("""
        SELECT month, avg_unit_price, median_unit_price,
               transaction_count, avg_rent_per_sqm, rent_to_price_ratio
        FROM district_stats
        WHERE city = ? AND district = ?
        ORDER BY month
    """, [city, district])

    return {
        "city": city,
        "district": district,
        "communities": communities,
        "txn_distribution": txn_distribution,
        "rent_distribution": rent_distribution,
        "price_trend": price_trend,
    }


def calculate_affordability(city: str, district: str, area: float = 90) -> dict:
    """计算购房负担指标"""
    # 最新房价
    latest = query_df("""
        SELECT avg_unit_price FROM district_stats
        WHERE city = ? AND district = ?
        ORDER BY month DESC LIMIT 1
    """, [city, district])

    # 收入数据
    income = query_df("""
        SELECT disposable_income FROM macro_data
        WHERE city = ? ORDER BY year DESC LIMIT 1
    """, [city])

    if latest.empty or income.empty:
        return None

    price_psm = latest.iloc[0]["avg_unit_price"]
    annual_income = income.iloc[0]["disposable_income"]

    total_price = price_psm * area
    # 房价收入比（双职工家庭）
    price_to_income = total_price / (annual_income * 2)
    # 月供收入比（30年商贷，30%首付）
    loan = total_price * 0.7
    monthly_rate = 0.037 / 12
    months = 360
    monthly_payment = loan * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)
    monthly_income = annual_income * 2 / 12
    payment_to_income = monthly_payment / monthly_income

    return {
        "price_per_sqm": round(price_psm),
        "total_price": round(total_price),
        "annual_household_income": round(annual_income * 2),
        "price_to_income_ratio": round(price_to_income, 1),
        "monthly_payment": round(monthly_payment),
        "monthly_household_income": round(monthly_income),
        "payment_to_income_ratio": round(payment_to_income, 2),
        "assessment": _assess_affordability(price_to_income),
    }


def _assess_affordability(ratio: float) -> str:
    if ratio <= 6:
        return "合理 - 大多数家庭可承受"
    elif ratio <= 10:
        return "偏高 - 需要一定经济基础"
    elif ratio <= 15:
        return "较高 - 购房压力较大"
    elif ratio <= 25:
        return "很高 - 购房压力很大"
    else:
        return "极高 - 普通家庭难以承受"
