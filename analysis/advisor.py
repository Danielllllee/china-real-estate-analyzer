"""投资分析模块 — 基于真实均价+租金数据"""
from core.database import query_df


def generate_district_report(city: str, district: str) -> dict:
    """获取区域数据（均价+租金+租售比）"""
    latest = query_df("""
        SELECT avg_unit_price, avg_rent_per_sqm, rent_to_price_ratio
        FROM district_stats
        WHERE city = ? AND district = ?
        ORDER BY month DESC LIMIT 1
    """, [city, district])

    if latest.empty:
        return {"error": "暂无该区域数据"}

    row = latest.iloc[0]
    result = {
        "city": city,
        "district": district,
        "avg_price": round(row["avg_unit_price"]),
    }
    if row["avg_rent_per_sqm"] is not None:
        result["rent_per_sqm"] = row["avg_rent_per_sqm"]
        result["annual_rent_yield"] = round(row["avg_rent_per_sqm"] * 12 / row["avg_unit_price"] * 100, 2)
    if row["rent_to_price_ratio"] is not None:
        result["rent_to_price_ratio"] = row["rent_to_price_ratio"]

    return result


def generate_city_summary(city: str) -> list:
    """生成城市所有区域的数据汇总"""
    districts = query_df("""
        SELECT district, avg_unit_price, avg_rent_per_sqm, rent_to_price_ratio
        FROM district_stats
        WHERE city = ? AND month = (SELECT MAX(month) FROM district_stats WHERE city = ?)
        ORDER BY avg_unit_price DESC
    """, [city, city])

    summaries = []
    for _, row in districts.iterrows():
        item = {
            "district": row["district"],
            "avg_price": round(row["avg_unit_price"]),
        }
        if row["avg_rent_per_sqm"] is not None:
            item["rent_per_sqm"] = row["avg_rent_per_sqm"]
            item["annual_rent_yield"] = round(
                row["avg_rent_per_sqm"] * 12 / row["avg_unit_price"] * 100, 2
            )
        summaries.append(item)

    return summaries
