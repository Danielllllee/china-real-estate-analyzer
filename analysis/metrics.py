"""核心分析指标计算 — 基于真实数据"""
import pandas as pd
from core.database import query_df


def get_city_overview(city: str) -> dict:
    """获取城市概览数据（均价+租金+租售比）"""
    latest_month = query_df("""
        SELECT MAX(month) as m FROM district_stats WHERE city = ?
    """, [city]).iloc[0]["m"]

    districts = query_df("""
        SELECT district, avg_unit_price, avg_rent_per_sqm, rent_to_price_ratio
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
        SELECT avg_unit_price, avg_rent_per_sqm, rent_to_price_ratio
        FROM district_stats
        WHERE city = ? AND district = ?
        ORDER BY month DESC LIMIT 1
    """, [city, district])

    if latest.empty:
        return {"city": city, "district": district, "latest_price": None}

    row = latest.iloc[0]
    return {
        "city": city,
        "district": district,
        "latest_price": row["avg_unit_price"],
        "rent_per_sqm": row["avg_rent_per_sqm"],
        "rent_to_price_ratio": row["rent_to_price_ratio"],
    }


def get_city_macro(city: str) -> dict:
    """获取城市宏观经济数据"""
    macro = query_df("""
        SELECT gdp, population, per_capita_income, data_year
        FROM macro_data WHERE city = ?
        ORDER BY data_year DESC LIMIT 1
    """, [city])

    if macro.empty:
        return None

    row = macro.iloc[0]
    return {
        "gdp": row["gdp"],
        "population": row["population"],
        "per_capita_income": row["per_capita_income"],
        "data_year": row["data_year"],
    }


def calculate_affordability(city: str) -> dict:
    """计算购房可负担性指标"""
    macro = get_city_macro(city)
    if not macro:
        return None

    # 获取城市均价
    avg = query_df("""
        SELECT AVG(avg_unit_price) as avg_price
        FROM district_stats
        WHERE city = ? AND month = (SELECT MAX(month) FROM district_stats WHERE city = ?)
    """, [city, city])

    if avg.empty or avg.iloc[0]["avg_price"] is None:
        return None

    avg_price = avg.iloc[0]["avg_price"]
    income = macro["per_capita_income"]

    # 房价收入比 = 90㎡总价 / 家庭年收入(按双职工)
    total_price_90 = avg_price * 90
    household_income = income * 2  # 双职工家庭
    price_income_ratio = total_price_90 / household_income if household_income > 0 else 0

    return {
        "city": city,
        "avg_price": round(avg_price),
        "per_capita_income": income,
        "household_income": household_income,
        "total_price_90sqm": round(total_price_90),
        "price_income_ratio": round(price_income_ratio, 1),
        "data_year": macro["data_year"],
    }
