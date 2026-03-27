"""跨城市/跨区域对比分析"""
from core.database import query_df


def compare_cities(cities: list) -> list:
    """多城市横向对比（均价+租金+宏观数据）"""
    results = []
    for city in cities:
        stats = query_df("""
            SELECT AVG(avg_unit_price) as avg_price,
                   AVG(avg_rent_per_sqm) as avg_rent
            FROM district_stats
            WHERE city = ? AND month = (
                SELECT MAX(month) FROM district_stats WHERE city = ?
            )
        """, [city, city])

        if stats.empty or stats.iloc[0]["avg_price"] is None:
            continue

        row = {
            "city": city,
            "avg_price": round(stats.iloc[0]["avg_price"]),
        }
        if stats.iloc[0]["avg_rent"] is not None:
            row["avg_rent"] = round(stats.iloc[0]["avg_rent"], 1)
            row["annual_yield"] = round(
                stats.iloc[0]["avg_rent"] * 12 / stats.iloc[0]["avg_price"] * 100, 2
            )

        # 宏观数据
        macro = query_df("""
            SELECT gdp, population, per_capita_income
            FROM macro_data WHERE city = ?
            ORDER BY data_year DESC LIMIT 1
        """, [city])
        if not macro.empty:
            row["gdp"] = macro.iloc[0]["gdp"]
            row["population"] = macro.iloc[0]["population"]
            row["per_capita_income"] = macro.iloc[0]["per_capita_income"]

        results.append(row)

    return results


def compare_districts(city: str):
    """同城市各区域对比（均价+租金）"""
    stats = query_df("""
        SELECT district, avg_unit_price, avg_rent_per_sqm, rent_to_price_ratio
        FROM district_stats
        WHERE city = ? AND month = (
            SELECT MAX(month) FROM district_stats WHERE city = ?
        )
        ORDER BY avg_unit_price DESC
    """, [city, city])

    return stats
