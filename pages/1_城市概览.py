"""城市概览页面 — Premium UI"""
import sys
import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.metrics import get_city_overview
from analysis.advisor import generate_city_summary
from utils.styles import (
    inject_global_css,
    hero_section,
    district_score_card,
    apply_plotly_style,
    PLOTLY_COLORS,
    PLOTLY_LAYOUT,
    COLORS,
)

st.set_page_config(page_title="城市概览", page_icon="🏙", layout="wide")

# ============ 全局样式 ============
inject_global_css()

# ============ Hero ============
hero_section("城市概览", "选择城市，一览各区域房价水平和投资价值")

# ============ 城市选择 ============
@st.cache_data
def load_config():
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()
city_names = {k: v["name"] for k, v in config["cities"].items()}

selected_city = st.selectbox(
    "选择城市",
    list(city_names.values()),
    label_visibility="collapsed",
)

# ============ 获取数据 ============
overview = get_city_overview(selected_city)

if overview["districts"].empty:
    st.warning("暂无该城市数据")
    st.stop()

st.markdown(
    f'<p style="text-align:center;color:{COLORS["text_light"]};margin-bottom:24px;">'
    f'数据截至 <b>{overview["latest_month"]}</b></p>',
    unsafe_allow_html=True,
)

# ============ 各区域投资评分 ============
st.markdown(
    f'<h2 style="color:{COLORS["primary"]};margin-bottom:4px;">各区域投资评分</h2>',
    unsafe_allow_html=True,
)

with st.spinner("正在分析各区域..."):
    summaries = generate_city_summary(selected_city)

if summaries:
    cols = st.columns(2)
    for idx, s in enumerate(summaries):
        with cols[idx % 2]:
            st.markdown(
                district_score_card(
                    district=s["district"],
                    score=s["score"],
                    price=s["avg_price"],
                    yield_pct=s["yield_pct"],
                    verdict=s["verdict"],
                    reason=s["verdict_reason"],
                ),
                unsafe_allow_html=True,
            )

st.markdown("---")

# ============ 图表分析 Tabs ============
districts = overview["districts"].sort_values("avg_unit_price", ascending=True)

tab1, tab2, tab3, tab4 = st.tabs(
    ["均价排名", "租售比分析", "成交活跃度", "价格走势"]
)

# --- Tab 1: 均价排名 ---
with tab1:
    fig_price = px.bar(
        districts,
        y="district",
        x="avg_unit_price",
        orientation="h",
        labels={"district": "区域", "avg_unit_price": "均价（元/㎡）"},
        color_discrete_sequence=PLOTLY_COLORS,
        text="avg_unit_price",
    )
    fig_price.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
    )
    apply_plotly_style(fig_price, height=max(360, len(districts) * 40))
    fig_price.update_layout(
        title=dict(text="各区域均价排名", font=dict(size=16)),
        yaxis=dict(title=""),
        xaxis=dict(title="均价（元/㎡）"),
    )
    st.plotly_chart(fig_price, use_container_width=True)

# --- Tab 2: 租售比分析 ---
with tab2:
    rtp_sorted = districts.sort_values("rent_to_price_ratio", ascending=False)
    fig_rtp = px.bar(
        rtp_sorted,
        x="district",
        y="rent_to_price_ratio",
        labels={"district": "区域", "rent_to_price_ratio": "租售比（年）"},
        color_discrete_sequence=PLOTLY_COLORS,
        text="rent_to_price_ratio",
    )
    fig_rtp.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside",
    )
    apply_plotly_style(fig_rtp, height=420)
    fig_rtp.update_layout(
        title=dict(text="租售比排名（越高性价比越好）", font=dict(size=16)),
        xaxis=dict(title=""),
        yaxis=dict(title="租售比（年）"),
    )
    st.plotly_chart(fig_rtp, use_container_width=True)

# --- Tab 3: 成交活跃度 ---
with tab3:
    txn_sorted = districts.sort_values("transaction_count", ascending=False)
    fig_txn = px.bar(
        txn_sorted,
        x="district",
        y="transaction_count",
        labels={"district": "区域", "transaction_count": "成交套数"},
        color_discrete_sequence=[PLOTLY_COLORS[1]],
        text="transaction_count",
    )
    fig_txn.update_traces(
        texttemplate="%{text:,}",
        textposition="outside",
    )
    apply_plotly_style(fig_txn, height=420)
    fig_txn.update_layout(
        title=dict(text="月度成交量", font=dict(size=16)),
        xaxis=dict(title=""),
        yaxis=dict(title="成交套数"),
    )
    st.plotly_chart(fig_txn, use_container_width=True)

# --- Tab 4: 价格走势 ---
with tab4:
    trend = overview["trend"]
    if not trend.empty:
        fig_trend = go.Figure()
        fig_trend.add_trace(
            go.Scatter(
                x=trend["month"],
                y=trend["city_avg_price"],
                mode="lines+markers",
                name="均价",
                line=dict(color=PLOTLY_COLORS[0], width=3),
                marker=dict(size=6, color=PLOTLY_COLORS[0]),
                fill="tozeroy",
                fillcolor=f"rgba(15,52,96,0.08)",
            )
        )
        apply_plotly_style(fig_trend, height=420)
        fig_trend.update_layout(
            title=dict(text=f"{selected_city} 均价走势", font=dict(size=16)),
            xaxis=dict(title="月份"),
            yaxis=dict(title="均价（元/㎡）"),
            hovermode="x unified",
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("暂无趋势数据")

st.markdown("---")

# ============ 数据明细 ============
st.markdown(
    f'<h2 style="color:{COLORS["primary"]};margin-bottom:12px;">数据明细</h2>',
    unsafe_allow_html=True,
)

display_df = overview["districts"][
    [
        "district",
        "avg_unit_price",
        "median_unit_price",
        "avg_rent_per_sqm",
        "rent_to_price_ratio",
        "transaction_count",
        "listing_count",
        "avg_deal_cycle",
    ]
].copy()
display_df.columns = [
    "区域",
    "均价(元/㎡)",
    "中位价(元/㎡)",
    "月租金(元/㎡)",
    "租售比(年)",
    "月成交量",
    "在售挂牌",
    "平均成交周期(天)",
]

st.dataframe(
    display_df.style.format(
        {
            "均价(元/㎡)": "{:,.0f}",
            "中位价(元/㎡)": "{:,.0f}",
            "月租金(元/㎡)": "{:.1f}",
            "租售比(年)": "{:.1f}",
            "月成交量": "{:,}",
            "在售挂牌": "{:,}",
            "平均成交周期(天)": "{:.0f}",
        }
    ),
    use_container_width=True,
    hide_index=True,
)
