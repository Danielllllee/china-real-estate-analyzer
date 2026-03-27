"""跨城市/跨区域对比分析"""
from core.database import query_df


def compare_cities(cities: list) -> dict:
    """多城市横向对比"""
    results = []
    for city in cities:
        # 最新数据
        stats = query_df("""
            SELECT AVG(avg_unit_price) as avg_price,
                   AVG(avg_rent_per_sqm) as avg_rent,
                   AVG(rent_to_price_ratio) as avg_rtp,
                   SUM(transaction_count) as total_txn,
                   AVG(avg_deal_cycle) as avg_cycle
            FROM district_stats
            WHERE city = ? AND month = (
                SELECT MAX(month) FROM district_stats WHERE city = ?
            )
        """, [city, city])

        macro = query_df("""
            SELECT population, gdp, disposable_income, gdp_growth
            FROM macro_data WHERE city = ?
            ORDER BY year DESC LIMIT 1
        """, [city])

        if stats.empty:
            continue

        row = stats.iloc[0].to_dict()
        row["city"] = city
        if not macro.empty:
            row.update(macro.iloc[0].to_dict())
            # 房价收入比
            if row.get("disposable_income") and row.get("avg_price"):
                row["price_to_income"] = round(row["avg_price"] * 90 / (row["disposable_income"] * 2), 1)
        results.append(row)

    return results


def compare_districts(city: str) -> list:
    """同城市各区域对比"""
    stats = query_df("""
        SELECT district, avg_unit_price, avg_rent_per_sqm,
               rent_to_price_ratio, transaction_count,
               listing_count, avg_deal_cycle
        FROM district_stats
        WHERE city = ? AND month = (
            SELECT MAX(month) FROM district_stats WHERE city = ?
        )
        ORDER BY rent_to_price_ratio DESC
    """, [city, city])

    return stats
