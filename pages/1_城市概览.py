"""城市概览页面"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.metrics import get_city_overview
from analysis.comparison import compare_districts
from analysis.advisor import generate_city_summary
import yaml

st.set_page_config(page_title="城市概览", page_icon="🏙️", layout="wide")
st.title("城市概览")

@st.cache_data
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()
city_names = {k: v["name"] for k, v in config["cities"].items()}
selected_city = st.selectbox("选择城市", list(city_names.values()))

overview = get_city_overview(selected_city)

if overview["districts"].empty:
    st.warning("暂无该城市数据")
    st.stop()

st.markdown(f"### {selected_city} — 数据截至 {overview['latest_month']}")

# ============ 新增：各区域投资建议总览 ============
st.subheader("各区域投资建议一览")
st.markdown("*综合租金回报、价格趋势、供需关系等多维度分析，给出每个区域的投资评价*")

with st.spinner("正在分析各区域..."):
    summaries = generate_city_summary(selected_city)

if summaries:
    for s in summaries:
        score = s["score"]
        if score >= 60:
            color = "🟢"
        elif score >= 45:
            color = "🟡"
        else:
            color = "🔴"

        col1, col2, col3, col4, col5 = st.columns([1.5, 1, 1, 1, 4])
        with col1:
            st.markdown(f"**{color} {s['district']}**")
        with col2:
            st.markdown(f"评分 **{score}**/100")
        with col3:
            st.markdown(f"均价 {s['avg_price']:,}")
        with col4:
            yield_str = f"{s['yield_pct']}%"
            st.markdown(f"租金回报 {yield_str}")
        with col5:
            st.markdown(f"{s['verdict']} — {s['verdict_reason'][:40]}...")

    st.markdown("---")

    # 评分可视化
    score_df = pd.DataFrame(summaries)
    fig_score = px.bar(
        score_df.sort_values("score"), x="score", y="district",
        orientation="h",
        labels={"district": "区域", "score": "投资评分"},
        color="score",
        color_continuous_scale="RdYlGn",
        range_color=[0, 100],
        title="各区域投资评分排名（满分100）",
    )
    fig_score.update_layout(height=max(300, len(summaries) * 35), showlegend=False)
    st.plotly_chart(fig_score, use_container_width=True)

# 各区域均价排名
st.subheader("各区域均价排名")
districts = overview["districts"].sort_values("avg_unit_price", ascending=True)

fig_price = px.bar(
    districts, y="district", x="avg_unit_price",
    orientation="h",
    labels={"district": "区域", "avg_unit_price": "均价（元/㎡）"},
    color="avg_unit_price",
    color_continuous_scale="RdYlGn_r",
)
fig_price.update_layout(height=max(300, len(districts) * 35), showlegend=False)
st.plotly_chart(fig_price, use_container_width=True)

# 核心指标对比
st.subheader("各区域核心指标")
col1, col2 = st.columns(2)

with col1:
    rtp_sorted = districts.sort_values("rent_to_price_ratio", ascending=False)
    fig_rtp = px.bar(
        rtp_sorted, x="district", y="rent_to_price_ratio",
        labels={"district": "区域", "rent_to_price_ratio": "租售比（年）"},
        title="租售比排名（越高性价比越好）",
        color="rent_to_price_ratio",
        color_continuous_scale="RdYlGn",
    )
    fig_rtp.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig_rtp, use_container_width=True)

with col2:
    fig_txn = px.bar(
        districts.sort_values("transaction_count", ascending=False),
        x="district", y="transaction_count",
        labels={"district": "区域", "transaction_count": "成交套数"},
        title="月度成交量",
        color="transaction_count",
        color_continuous_scale="Blues",
    )
    fig_txn.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig_txn, use_container_width=True)

# 价格趋势
st.subheader("城市均价走势")
trend = overview["trend"]
if not trend.empty:
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=trend["month"], y=trend["city_avg_price"],
        mode="lines+markers", name="均价",
        line=dict(color="#1f77b4", width=2),
    ))
    fig_trend.update_layout(
        xaxis_title="月份", yaxis_title="均价（元/㎡）",
        height=400, hovermode="x unified",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# 数据表格
st.subheader("各区域详细数据")
display_df = overview["districts"][["district", "avg_unit_price", "median_unit_price",
                                     "avg_rent_per_sqm", "rent_to_price_ratio",
                                     "transaction_count", "listing_count", "avg_deal_cycle"]]
display_df.columns = ["区域", "均价(元/㎡)", "中位价(元/㎡)", "月租金(元/㎡)",
                       "租售比(年)", "月成交量", "在售挂牌", "平均成交周期(天)"]
st.dataframe(display_df, use_container_width=True, hide_index=True)
