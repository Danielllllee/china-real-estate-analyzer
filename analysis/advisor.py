"""投资分析模块 — 当前仅有均价数据，暂不提供投资建议"""
from core.database import query_df


def generate_district_report(city: str, district: str) -> dict:
    """获取区域数据（仅均价）"""
    latest = query_df("""
        SELECT avg_unit_price FROM district_stats
        WHERE city = ? AND district = ?
        ORDER BY month DESC LIMIT 1
    """, [city, district])

    if latest.empty:
        return {"error": "暂无该区域数据"}

    avg_price = latest.iloc[0]["avg_unit_price"]

    return {
        "city": city,
        "district": district,
        "avg_price": round(avg_price),
    }


def generate_city_summary(city: str) -> list:
    """生成城市所有区域的数据汇总（仅均价）"""
    districts = query_df("""
        SELECT district, avg_unit_price FROM district_stats
        WHERE city = ? AND month = (SELECT MAX(month) FROM district_stats WHERE city = ?)
        ORDER BY avg_unit_price DESC
    """, [city, city])

    summaries = []
    for _, row in districts.iterrows():
        summaries.append({
            "district": row["district"],
            "avg_price": round(row["avg_unit_price"]),
        })

    return summaries
