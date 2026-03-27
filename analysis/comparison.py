"""跨城市/跨区域对比分析"""
from core.database import query_df


def compare_cities(cities: list) -> dict:
    """多城市横向对比（仅基于真实均价数据）"""
    results = []
    for city in cities:
        stats = query_df("""
            SELECT AVG(avg_unit_price) as avg_price
            FROM district_stats
            WHERE city = ? AND month = (
                SELECT MAX(month) FROM district_stats WHERE city = ?
            )
        """, [city, city])

        if stats.empty or stats.iloc[0]["avg_price"] is None:
            continue

        row = {"city": city, "avg_price": round(stats.iloc[0]["avg_price"])}
        results.append(row)

    return results


def compare_districts(city: str):
    """同城市各区域对比（仅均价）"""
    stats = query_df("""
        SELECT district, avg_unit_price
        FROM district_stats
        WHERE city = ? AND month = (
            SELECT MAX(month) FROM district_stats WHERE city = ?
        )
        ORDER BY avg_unit_price DESC
    """, [city, city])

    return stats
