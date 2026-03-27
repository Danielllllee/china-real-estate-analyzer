"""风险评估模块"""
from core.database import query_df


def assess_market_risk(city: str, district: str) -> dict:
    """评估区域市场风险"""
    # 价格波动（近3年标准差/均值）
    prices = query_df("""
        SELECT avg_unit_price FROM district_stats
        WHERE city = ? AND district = ?
        AND month >= date('now', '-3 years')
        ORDER BY month
    """, [city, district])

    if prices.empty or len(prices) < 6:
        return {"error": "数据不足"}

    price_series = prices["avg_unit_price"]
    volatility = price_series.std() / price_series.mean()

    # 价格趋势（近12个月 vs 前12个月）
    recent = price_series.tail(12).mean()
    earlier = price_series.head(12).mean()
    trend = (recent - earlier) / earlier

    # 成交量趋势
    volume = query_df("""
        SELECT month, transaction_count FROM district_stats
        WHERE city = ? AND district = ?
        AND month >= date('now', '-2 years')
        ORDER BY month
    """, [city, district])

    vol_trend = 0
    if not volume.empty and len(volume) >= 12:
        recent_vol = volume["transaction_count"].tail(6).mean()
        earlier_vol = volume["transaction_count"].head(6).mean()
        if earlier_vol > 0:
            vol_trend = (recent_vol - earlier_vol) / earlier_vol

    # 挂牌去化周期
    latest = query_df("""
        SELECT listing_count, transaction_count FROM district_stats
        WHERE city = ? AND district = ?
        ORDER BY month DESC LIMIT 1
    """, [city, district])

    months_of_inventory = 0
    if not latest.empty:
        lc = latest.iloc[0]["listing_count"]
        tc = latest.iloc[0]["transaction_count"]
        if tc > 0:
            months_of_inventory = lc / tc

    # 风险评分（0-100，越高越有风险）
    risk_score = 0
    risk_factors = []

    if volatility > 0.15:
        risk_score += 25
        risk_factors.append("价格波动较大")
    elif volatility > 0.08:
        risk_score += 10

    if trend < -0.10:
        risk_score += 25
        risk_factors.append("价格下行趋势明显")
    elif trend < -0.03:
        risk_score += 10
        risk_factors.append("价格略有下行")

    if vol_trend < -0.30:
        risk_score += 20
        risk_factors.append("成交量大幅萎缩")
    elif vol_trend < -0.10:
        risk_score += 10

    if months_of_inventory > 12:
        risk_score += 20
        risk_factors.append("库存去化周期过长")
    elif months_of_inventory > 6:
        risk_score += 10

    if risk_score <= 20:
        risk_level = "低风险"
    elif risk_score <= 40:
        risk_level = "中低风险"
    elif risk_score <= 60:
        risk_level = "中等风险"
    elif risk_score <= 80:
        risk_level = "较高风险"
    else:
        risk_level = "高风险"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "volatility": round(volatility, 4),
        "price_trend_12m": round(trend, 4),
        "volume_trend": round(vol_trend, 4),
        "months_of_inventory": round(months_of_inventory, 1),
    }
