"""智能投资解读模块

为每个区域生成「是否值得买入」的解读报告，
包含明确的结论、理由、风险提示和具体板块建议。
面向小白用户，语言通俗易懂。
"""
from core.database import query_df
from analysis.risk import assess_market_risk
from analysis.metrics import calculate_affordability


def generate_district_report(city: str, district: str) -> dict:
    """生成区域投资解读报告

    Returns:
        包含结论、评分、理由、风险、板块建议、历史案例的完整报告
    """
    # ---- 1. 采集所有原始数据 ----
    # 最新区域统计
    latest = query_df("""
        SELECT * FROM district_stats
        WHERE city = ? AND district = ?
        ORDER BY month DESC LIMIT 1
    """, [city, district])

    if latest.empty:
        return {"error": "暂无该区域数据"}

    stats = latest.iloc[0]
    avg_price = stats["avg_unit_price"]
    avg_rent = stats["avg_rent_per_sqm"]
    rtp = stats["rent_to_price_ratio"]
    txn_count = stats["transaction_count"]
    listing_count = stats["listing_count"]
    avg_cycle = stats["avg_deal_cycle"]

    # 价格趋势
    trend = query_df("""
        SELECT month, avg_unit_price FROM district_stats
        WHERE city = ? AND district = ?
        ORDER BY month
    """, [city, district])

    # 板块数据
    sectors = query_df("""
        SELECT sector_name, avg_unit_price, avg_rent_per_sqm, community_count
        FROM sectors
        WHERE city = ? AND district = ?
        ORDER BY avg_unit_price DESC
    """, [city, district])

    # 历史案例
    cases = query_df("""
        SELECT * FROM deal_cases
        WHERE city = ? AND district = ?
        ORDER BY deal_year DESC
    """, [city, district])

    # 风险评估
    risk = assess_market_risk(city, district)

    # 负担能力
    afford = calculate_affordability(city, district)

    # 宏观
    macro = query_df("""
        SELECT * FROM macro_data
        WHERE city = ? ORDER BY year DESC LIMIT 1
    """, [city])

    # ---- 2. 计算核心指标 ----
    # 年化租金回报率
    annual_yield = (avg_rent * 12) / avg_price if avg_price > 0 else 0

    # 价格变化趋势
    price_trend_1y = 0
    price_trend_3y = 0
    if len(trend) >= 12:
        recent_12 = trend["avg_unit_price"].tail(12).mean()
        earlier_12 = trend["avg_unit_price"].iloc[:-12].tail(12).mean() if len(trend) >= 24 else trend["avg_unit_price"].head(12).mean()
        price_trend_1y = (recent_12 - earlier_12) / earlier_12 if earlier_12 > 0 else 0
    if len(trend) >= 36:
        recent = trend["avg_unit_price"].tail(12).mean()
        three_yr_ago = trend["avg_unit_price"].head(12).mean()
        price_trend_3y = (recent - three_yr_ago) / three_yr_ago if three_yr_ago > 0 else 0

    # 供需关系：挂牌去化比
    months_of_supply = listing_count / txn_count if txn_count > 0 else 99

    # ---- 3. 综合评分（0-100） ----
    score = 50  # 基准分
    score_details = []

    # 租金回报率评分（权重高，第一性原理核心）
    if annual_yield >= 0.04:
        score += 15
        score_details.append(("租金回报率优秀", f"年化{annual_yield*100:.1f}%，超过4%的合理水平", "+15"))
    elif annual_yield >= 0.03:
        score += 8
        score_details.append(("租金回报率尚可", f"年化{annual_yield*100:.1f}%，接近合理水平", "+8"))
    elif annual_yield >= 0.02:
        score -= 5
        score_details.append(("租金回报率偏低", f"年化{annual_yield*100:.1f}%，低于3%存在泡沫风险", "-5"))
    else:
        score -= 15
        score_details.append(("租金回报率极低", f"年化{annual_yield*100:.1f}%，严重依赖资本增值", "-15"))

    # 价格趋势评分
    if price_trend_1y > 0.05:
        score += 5
        score_details.append(("价格上行趋势", f"近一年涨幅{price_trend_1y*100:.1f}%", "+5"))
    elif price_trend_1y < -0.05:
        score -= 8
        score_details.append(("价格下行趋势", f"近一年跌幅{abs(price_trend_1y)*100:.1f}%，可能继续探底", "-8"))
    elif price_trend_1y < -0.10:
        score -= 15
        score_details.append(("价格大幅下跌", f"近一年跌幅{abs(price_trend_1y)*100:.1f}%，市场信心不足", "-15"))
    else:
        score_details.append(("价格基本横盘", f"近一年变动{price_trend_1y*100:.1f}%", "0"))

    # 供需关系评分
    if months_of_supply < 4:
        score += 10
        score_details.append(("供不应求", f"去化周期仅{months_of_supply:.1f}个月，卖方市场", "+10"))
    elif months_of_supply < 8:
        score += 3
        score_details.append(("供需平衡", f"去化周期{months_of_supply:.1f}个月", "+3"))
    elif months_of_supply < 15:
        score -= 5
        score_details.append(("供过于求", f"去化周期{months_of_supply:.1f}个月，买方有议价空间", "-5"))
    else:
        score -= 12
        score_details.append(("严重供过于求", f"去化周期{months_of_supply:.1f}个月，库存积压严重", "-12"))

    # 成交活跃度
    if txn_count > 100:
        score += 5
        score_details.append(("市场活跃", f"月成交{txn_count}套，流动性好", "+5"))
    elif txn_count < 30:
        score -= 5
        score_details.append(("成交冷淡", f"月成交仅{txn_count}套，流动性差", "-5"))

    # 成交周期
    if avg_cycle and avg_cycle < 60:
        score += 3
        score_details.append(("成交快速", f"平均{avg_cycle}天成交", "+3"))
    elif avg_cycle and avg_cycle > 120:
        score -= 5
        score_details.append(("成交缓慢", f"平均{avg_cycle}天才能成交，变现困难", "-5"))

    # 购房负担
    if afford:
        pti = afford["price_to_income_ratio"]
        if pti <= 10:
            score += 5
            score_details.append(("购房负担合理", f"房价收入比{pti}，当地居民可承受", "+5"))
        elif pti > 20:
            score -= 8
            score_details.append(("购房负担极重", f"房价收入比高达{pti}，脱离当地收入水平", "-8"))
        elif pti > 15:
            score -= 3
            score_details.append(("购房负担较重", f"房价收入比{pti}", "-3"))

    score = max(0, min(100, score))

    # ---- 4. 生成结论 ----
    if score >= 75:
        verdict = "强烈推荐买入"
        verdict_emoji = "🟢"
        verdict_reason = "该区域租金回报率高、供需健康、价格合理，具有明确的投资价值。"
    elif score >= 60:
        verdict = "可以考虑买入"
        verdict_emoji = "🟡"
        verdict_reason = "该区域整体面尚可，但部分指标存在隐忧，建议精选板块和小区。"
    elif score >= 45:
        verdict = "谨慎观望"
        verdict_emoji = "🟠"
        verdict_reason = "该区域当前不具备明显的投资吸引力，建议等待价格进一步回调或市场企稳。"
    elif score >= 30:
        verdict = "不建议买入"
        verdict_emoji = "🔴"
        verdict_reason = "该区域多项指标亮红灯，投资风险较高，除非有刚需否则不建议。"
    else:
        verdict = "强烈不建议"
        verdict_emoji = "⛔"
        verdict_reason = "该区域存在严重的估值泡沫或市场下行风险，请远离。"

    # ---- 5. 板块推荐 ----
    sector_recommendations = []
    if not sectors.empty:
        for _, s in sectors.iterrows():
            s_yield = (s["avg_rent_per_sqm"] * 12) / s["avg_unit_price"] if s["avg_unit_price"] > 0 else 0
            recommendation = "值得关注" if s_yield >= 0.025 else "性价比一般"
            if s_yield >= 0.035:
                recommendation = "重点推荐"
            sector_recommendations.append({
                "name": s["sector_name"],
                "avg_price": round(s["avg_unit_price"]),
                "avg_rent": round(s["avg_rent_per_sqm"], 1),
                "yield_pct": round(s_yield * 100, 2),
                "community_count": s["community_count"],
                "recommendation": recommendation,
            })

    # ---- 6. 典型案例解读 ----
    case_stories = []
    if not cases.empty:
        for _, c in cases.iterrows():
            profit = c["profit_loss_wan"]
            ret = c["annualized_return"]
            if profit > 0:
                outcome = f"盈利{profit:.1f}万元，年化回报{ret:.1f}%"
            elif profit < 0:
                outcome = f"亏损{abs(profit):.1f}万元，年化回报{ret:.1f}%"
            else:
                outcome = "基本持平"

            story = (
                f"【{c['sector_name']}·{c['community_name']}】"
                f"{c['deal_year']}年买入{c['area']:.0f}㎡{c['bedroom_count']}房，"
                f"总价{c['total_price_wan']:.1f}万（单价{c['unit_price']:,.0f}元/㎡）→ "
                f"当前估值约{c['current_value_wan']:.1f}万，{outcome}"
            )
            case_stories.append({
                "year": c["deal_year"],
                "sector": c["sector_name"],
                "community": c["community_name"],
                "story": story,
                "profit": profit,
                "return_pct": ret,
            })

    # ---- 7. 组装完整报告 ----
    # 生成大白话解读
    plain_text = _generate_plain_text(
        city, district, avg_price, annual_yield, price_trend_1y,
        months_of_supply, score, verdict, afford, sector_recommendations,
        case_stories, risk,
    )

    return {
        "city": city,
        "district": district,
        "score": score,
        "verdict": verdict,
        "verdict_emoji": verdict_emoji,
        "verdict_reason": verdict_reason,
        "score_details": score_details,
        "key_metrics": {
            "avg_price": round(avg_price),
            "annual_yield_pct": round(annual_yield * 100, 2),
            "price_trend_1y_pct": round(price_trend_1y * 100, 1),
            "price_trend_3y_pct": round(price_trend_3y * 100, 1),
            "months_of_supply": round(months_of_supply, 1),
            "txn_count": txn_count,
            "avg_cycle": avg_cycle,
        },
        "affordability": afford,
        "risk": risk if "error" not in risk else None,
        "sector_recommendations": sector_recommendations,
        "case_stories": case_stories,
        "plain_text_report": plain_text,
    }


def _generate_plain_text(
    city, district, avg_price, annual_yield, price_trend_1y,
    months_of_supply, score, verdict, afford, sectors, cases, risk,
):
    """生成面向小白的大白话解读"""
    lines = []
    lines.append(f"## {city}·{district} — 买房值不值？")
    lines.append("")

    # 一句话结论
    if score >= 60:
        lines.append(f"**一句话结论：当前{district}的房子整体{verdict}。**")
    else:
        lines.append(f"**一句话结论：当前{district}的房子{verdict}。**")
    lines.append("")

    # 价格水平
    lines.append(f"### 现在这里的房价是多少？")
    lines.append(f"当前{district}均价约**{avg_price:,.0f}元/㎡**。"
                 f"也就是说，一套90㎡的三居室大约要**{avg_price*90/10000:.0f}万元**。")
    lines.append("")

    # 租金回报
    lines.append(f"### 买了能赚钱吗？")
    if annual_yield >= 0.035:
        lines.append(f"从租金角度看，年化回报率**{annual_yield*100:.1f}%**，相当不错。"
                     f"意味着你买房出租，每年能收回房价的{annual_yield*100:.1f}%。"
                     f"这个水平已经接近甚至超过很多理财产品。")
    elif annual_yield >= 0.025:
        lines.append(f"从租金角度看，年化回报率**{annual_yield*100:.1f}%**，中规中矩。"
                     f"光靠租金回本大约需要{1/annual_yield:.0f}年。"
                     f"这意味着你买房不能只指望租金，还需要房价上涨才能真正赚钱。")
    else:
        lines.append(f"从租金角度看，年化回报率仅**{annual_yield*100:.1f}%**，非常低。"
                     f"光靠租金回本需要{1/annual_yield:.0f}年以上。"
                     f"说白了，这里的房价相对于租金来说太贵了，"
                     f"如果房价不涨甚至下跌，投资就会亏损。")
    lines.append("")

    # 价格趋势
    lines.append(f"### 房价是涨是跌？")
    if price_trend_1y > 0.03:
        lines.append(f"过去一年房价上涨了约**{price_trend_1y*100:.1f}%**，市场处于上行阶段。")
    elif price_trend_1y < -0.03:
        lines.append(f"过去一年房价下跌了约**{abs(price_trend_1y)*100:.1f}%**。"
                     f"这意味着如果你一年前买了，现在账面上已经亏了。"
                     f"当然，下跌也可能意味着更好的买入机会——关键看是否已经跌到位。")
    else:
        lines.append(f"过去一年房价基本持平（变动{price_trend_1y*100:.1f}%），处于横盘阶段。")
    lines.append("")

    # 市场供需
    lines.append(f"### 好不好卖？")
    if months_of_supply < 5:
        lines.append(f"当前挂牌库存去化周期约**{months_of_supply:.1f}个月**，市场偏紧。"
                     f"房子挂出去比较容易卖掉，作为买家议价空间较小。")
    elif months_of_supply < 10:
        lines.append(f"当前库存去化约**{months_of_supply:.1f}个月**，供需基本平衡。"
                     f"不会太难卖，但也别指望一挂就卖。")
    else:
        lines.append(f"当前库存去化高达**{months_of_supply:.1f}个月**，市场上房子很多。"
                     f"这对买家是好事——选择多、可以慢慢挑、大胆砍价。"
                     f"但也说明如果你将来要卖，可能也不好卖。")
    lines.append("")

    # 负担能力
    if afford:
        lines.append(f"### 当地人买得起吗？")
        pti = afford["price_to_income_ratio"]
        if pti <= 10:
            lines.append(f"房价收入比**{pti}**（意思是一个家庭不吃不喝{pti:.0f}年能买一套90㎡的房子），"
                         f"相对当地收入水平还算合理。")
        elif pti <= 20:
            lines.append(f"房价收入比**{pti}**，也就是说一个家庭需要不吃不喝{pti:.0f}年才能买一套房。"
                         f"购房压力不小，但在中国主要城市中算中等水平。")
        else:
            lines.append(f"房价收入比高达**{pti}**，严重脱离当地收入水平。"
                         f"普通家庭不吃不喝要{pti:.0f}年才能买一套房。"
                         f"这种价格水平很难靠本地刚需支撑，风险较高。")
        lines.append("")

    # 板块推荐
    if sectors:
        lines.append(f"### 具体哪些板块值得看？")
        for s in sectors[:5]:
            tag = ""
            if s["recommendation"] == "重点推荐":
                tag = "⭐ "
            elif s["recommendation"] == "值得关注":
                tag = "👀 "
            lines.append(f"- {tag}**{s['name']}**：均价{s['avg_price']:,}元/㎡，"
                         f"租金回报{s['yield_pct']}%，{s['recommendation']}")
        lines.append("")

    # 历史案例
    if cases:
        lines.append(f"### 以前买的人赚了还是亏了？")
        # 按年份分组展示
        profit_cases = [c for c in cases if c["profit"] > 0]
        loss_cases = [c for c in cases if c["profit"] <= 0]

        if profit_cases:
            lines.append(f"**赚钱的案例（{len(profit_cases)}个）：**")
            for c in profit_cases[:3]:
                lines.append(f"- {c['story']}")

        if loss_cases:
            lines.append(f"**亏损的案例（{len(loss_cases)}个）：**")
            for c in loss_cases[:3]:
                lines.append(f"- {c['story']}")
        lines.append("")

    # 风险提示
    if risk and "error" not in risk and risk.get("risk_factors"):
        lines.append(f"### 风险提示")
        for rf in risk["risk_factors"]:
            lines.append(f"- ⚠️ {rf}")
        lines.append("")

    # 最终建议
    lines.append(f"### 综合建议")
    lines.append(f"综合评分：**{score}/100分**")
    lines.append("")
    if score >= 60:
        lines.append(f"如果你有自住需求且预算匹配，{district}是可以考虑的选择。"
                     f"建议优先关注租金回报率较高的板块，选择次新房（5-10年房龄），"
                     f"并在当前市场多看多比较，争取议价空间。")
    elif score >= 45:
        lines.append(f"当前{district}处于调整期，不建议着急入手。"
                     f"如果确实有需求，建议再等3-6个月观察市场走势，"
                     f"或者关注区域内价格已经回调到位的优质板块。")
    else:
        lines.append(f"当前{district}的投资性价比较低，风险大于机会。"
                     f"除非有不可替代的自住需求，否则建议将资金配置到其他更有价值的区域。")

    return "\n".join(lines)


def generate_city_summary(city: str) -> list:
    """生成城市所有区域的投资建议汇总"""
    districts = query_df("""
        SELECT DISTINCT district FROM district_stats
        WHERE city = ? ORDER BY district
    """, [city])

    summaries = []
    for _, row in districts.iterrows():
        report = generate_district_report(city, row["district"])
        if "error" not in report:
            summaries.append({
                "district": row["district"],
                "score": report["score"],
                "verdict": report["verdict"],
                "verdict_emoji": report["verdict_emoji"],
                "avg_price": report["key_metrics"]["avg_price"],
                "yield_pct": report["key_metrics"]["annual_yield_pct"],
                "trend_1y": report["key_metrics"]["price_trend_1y_pct"],
                "verdict_reason": report["verdict_reason"],
            })

    # 按评分排序
    summaries.sort(key=lambda x: x["score"], reverse=True)
    return summaries
