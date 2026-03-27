"""区域深度分析页面 — 含智能解读、板块分析、历史案例"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.metrics import get_district_detail, calculate_affordability
from analysis.risk import assess_market_risk
from analysis.advisor import generate_district_report
from models.composite import composite_valuation
import yaml

st.set_page_config(page_title="区域分析", page_icon="📊", layout="wide")
st.title("区域深度分析")

@st.cache_data
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

city_names = {k: v["name"] for k, v in config["cities"].items()}
selected_city = st.selectbox("选择城市", list(city_names.values()))
city_key = [k for k, v in config["cities"].items() if v["name"] == selected_city][0]
district_names = [d["name"] for d in config["cities"][city_key]["districts"]]
selected_district = st.selectbox("选择区域", district_names)

# ============ 智能解读报告 ============
st.markdown("---")
with st.spinner("正在生成智能分析报告..."):
    report = generate_district_report(selected_city, selected_district)

if "error" in report:
    st.warning(report["error"])
    st.stop()

# 顶部结论卡片
st.markdown(f"## {report['verdict_emoji']} {selected_city}·{selected_district} — {report['verdict']}")
st.markdown(f"**综合评分：{report['score']}/100** | {report['verdict_reason']}")

# 关键指标
metrics = report["key_metrics"]
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("均价", f"{metrics['avg_price']:,}元/㎡")
with col2:
    st.metric("租金回报率", f"{metrics['annual_yield_pct']}%")
with col3:
    st.metric("近1年涨跌", f"{metrics['price_trend_1y_pct']:+.1f}%")
with col4:
    st.metric("去化周期", f"{metrics['months_of_supply']}月")
with col5:
    st.metric("月成交量", f"{metrics['txn_count']}套")

# ============ 大白话解读报告 ============
st.markdown("---")
st.subheader("完整分析报告")
with st.expander("展开查看详细解读（小白友好版）", expanded=True):
    st.markdown(report["plain_text_report"])

# ============ 评分明细 ============
st.markdown("---")
st.subheader("评分明细")
score_df = pd.DataFrame(report["score_details"], columns=["指标", "说明", "分数"])
st.dataframe(score_df, use_container_width=True, hide_index=True)

# 评分雷达图 / 仪表盘
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=report["score"],
    title={"text": "综合投资评分"},
    gauge={
        "axis": {"range": [0, 100]},
        "bar": {"color": "#1f77b4"},
        "steps": [
            {"range": [0, 30], "color": "#ff4444"},
            {"range": [30, 45], "color": "#ff8800"},
            {"range": [45, 60], "color": "#ffcc00"},
            {"range": [60, 75], "color": "#88cc00"},
            {"range": [75, 100], "color": "#00cc44"},
        ],
    },
))
fig_gauge.update_layout(height=250)
st.plotly_chart(fig_gauge, use_container_width=True)

# ============ 板块级分析 ============
st.markdown("---")
st.subheader("板块级分析")
st.markdown("*同一个区下面不同板块的房价和性价比差异很大，以下是各板块的对比：*")

sectors = report["sector_recommendations"]
if sectors:
    sector_df = pd.DataFrame(sectors)

    # 板块对比图
    col1, col2 = st.columns(2)
    with col1:
        fig_sp = px.bar(
            sector_df.sort_values("avg_price"),
            y="name", x="avg_price", orientation="h",
            color="yield_pct",
            color_continuous_scale="RdYlGn",
            labels={"name": "板块", "avg_price": "均价（元/㎡）", "yield_pct": "租金回报%"},
            title="各板块均价及租金回报率",
        )
        fig_sp.update_layout(height=max(250, len(sectors) * 40), showlegend=False)
        st.plotly_chart(fig_sp, use_container_width=True)

    with col2:
        fig_sy = px.bar(
            sector_df.sort_values("yield_pct", ascending=True),
            y="name", x="yield_pct", orientation="h",
            color="recommendation",
            color_discrete_map={"重点推荐": "#00cc44", "值得关注": "#ffcc00", "性价比一般": "#ff8800"},
            labels={"name": "板块", "yield_pct": "租金回报率（%）"},
            title="各板块租金回报率排名",
        )
        fig_sy.update_layout(height=max(250, len(sectors) * 40))
        st.plotly_chart(fig_sy, use_container_width=True)

    # 板块详细表格
    display_sectors = sector_df.copy()
    display_sectors.columns = ["板块", "均价(元/㎡)", "月租金(元/㎡)", "租金回报(%)", "小区数", "投资建议"]
    st.dataframe(display_sectors, use_container_width=True, hide_index=True)
else:
    st.info("暂无板块级数据")

# ============ 历史成交案例 ============
st.markdown("---")
st.subheader("历史成交案例 — 以前买的人赚了还是亏了？")
st.markdown("*以下是该区域真实的历史成交案例，帮你直观了解不同时期买入的实际回报：*")

cases = report["case_stories"]
if cases:
    # 按盈亏分组
    profit_cases = [c for c in cases if c["profit"] > 0]
    loss_cases = [c for c in cases if c["profit"] <= 0]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"#### 赚钱的案例（{len(profit_cases)}个）")
        for c in profit_cases[:6]:
            with st.container():
                st.markdown(f"**{c['sector']}·{c['community']}** | {c['year']}年买入")
                profit_color = "green"
                st.markdown(f":{profit_color}[盈利 {c['profit']:.1f}万 | 年化 {c['return_pct']}%]")
                st.caption(c["story"])
                st.markdown("---")

    with col2:
        st.markdown(f"#### 亏损的案例（{len(loss_cases)}个）")
        for c in loss_cases[:6]:
            with st.container():
                st.markdown(f"**{c['sector']}·{c['community']}** | {c['year']}年买入")
                st.markdown(f":red[亏损 {abs(c['profit']):.1f}万 | 年化 {c['return_pct']}%]")
                st.caption(c["story"])
                st.markdown("---")

    # 案例回报可视化
    case_df = pd.DataFrame(cases)
    if not case_df.empty:
        fig_cases = px.scatter(
            case_df, x="year", y="return_pct",
            size=[abs(p) + 1 for p in case_df["profit"]],
            color=["盈利" if p > 0 else "亏损" for p in case_df["profit"]],
            color_discrete_map={"盈利": "#00cc44", "亏损": "#ff4444"},
            hover_data=["sector", "community", "profit"],
            labels={"year": "买入年份", "return_pct": "年化回报率(%)", "color": "盈亏"},
            title="不同年份买入的年化回报率分布",
        )
        fig_cases.update_layout(height=400)
        st.plotly_chart(fig_cases, use_container_width=True)
else:
    st.info("暂无历史案例数据")

# ============ 风险评估 ============
st.markdown("---")
st.subheader("市场风险评估")
risk = report.get("risk")
if risk:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("风险评分", f"{risk['risk_score']}/100")
    with col2:
        st.metric("风险等级", risk["risk_level"])
    with col3:
        st.metric("价格波动率", f"{risk['volatility']*100:.1f}%")
    with col4:
        st.metric("库存去化月数", f"{risk['months_of_inventory']:.1f}")
    if risk.get("risk_factors"):
        for rf in risk["risk_factors"]:
            st.warning(f"⚠️ {rf}")

# ============ 购房负担 ============
afford = report.get("affordability")
if afford:
    st.subheader("购房负担分析")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("90㎡总价", f"{afford['total_price']/10000:.0f}万元")
    with col2:
        st.metric("房价收入比", f"{afford['price_to_income_ratio']}")
    with col3:
        st.metric("月供收入比", f"{afford['payment_to_income_ratio']:.0%}")
    st.info(afford["assessment"])

# ============ 估值分析 ============
st.markdown("---")
st.subheader("综合估值分析")
detail = get_district_detail(selected_city, selected_district)

if not detail["communities"].empty:
    valuation = composite_valuation(
        selected_city, selected_district,
        current_price_per_sqm=detail["communities"]["avg_listing_price"].median(),
    )
    if "error" not in valuation:
        comp = valuation["composite"]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("保守估值", f"{comp['conservative_value']:,}元/㎡")
        with col2:
            st.metric("中性估值", f"{comp['fair_value_per_sqm']:,}元/㎡")
        with col3:
            st.metric("乐观估值", f"{comp['optimistic_value']:,}元/㎡")

        if "composite_assessment" in valuation:
            ca = valuation["composite_assessment"]
            st.info(f"**{ca['recommendation']}** | 当前挂牌价偏离综合估值 {ca['deviation_pct']}")

# 价格趋势
st.subheader("价格趋势")
pt = detail["price_trend"]
if not pt.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=pt["month"], y=pt["avg_unit_price"], mode="lines", name="均价"))
    fig.add_trace(go.Scatter(x=pt["month"], y=pt["median_unit_price"], mode="lines", name="中位价", line=dict(dash="dash")))
    fig.update_layout(height=350, yaxis_title="元/㎡", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# 小区列表
st.subheader("区域内小区")
if not detail["communities"].empty:
    comm = detail["communities"][["name", "build_year", "avg_listing_price", "listing_count", "property_fee"]]
    comm.columns = ["小区名称", "建成年份", "挂牌均价(元/㎡)", "在售套数", "物业费(元/㎡/月)"]
    comm = comm.sort_values("挂牌均价(元/㎡)", ascending=False)
    st.dataframe(comm, use_container_width=True, hide_index=True)
