"""房价与购房可负担性总览 — 基于真实宏观数据"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.database import query_df
from analysis.metrics import calculate_affordability
from core.styles import inject_global_css, hero_section, apply_plotly_style, PLOTLY_COLORS, COLORS

st.set_page_config(page_title="购房可负担性", page_icon="📈", layout="wide")
inject_global_css()
hero_section("购房可负担性分析", "基于真实房价与居民收入数据的可负担性对比")

# ── 获取所有城市 ──
cities = query_df("SELECT DISTINCT city FROM macro_data ORDER BY gdp DESC")

if cities.empty:
    st.warning("暂无宏观数据")
    st.stop()

# ── 计算各城市可负担性 ──
affordability_data = []
for city in cities["city"]:
    result = calculate_affordability(city)
    if result:
        affordability_data.append(result)

if not affordability_data:
    st.warning("无法计算可负担性数据")
    st.stop()

df = pd.DataFrame(affordability_data)

# ── 房价收入比排名 ──
st.markdown(f'<h3 style="color:{COLORS["primary"]};">各城市房价收入比排名</h3>', unsafe_allow_html=True)
st.caption("房价收入比 = 90㎡住房总价 / 双职工家庭年收入。数值越高，购房压力越大。")

fig_ratio = px.bar(
    df.sort_values("price_income_ratio", ascending=True),
    y="city", x="price_income_ratio", orientation="h",
    labels={"city": "城市", "price_income_ratio": "房价收入比"},
    color_discrete_sequence=["#f59e0b"],
    text="price_income_ratio",
)
fig_ratio.update_traces(texttemplate="%{text:.1f}", textposition="outside")
apply_plotly_style(fig_ratio, max(400, len(df) * 35))
fig_ratio.update_layout(yaxis_title="", xaxis_title="房价收入比（90㎡/双职工年收入）")
st.plotly_chart(fig_ratio, use_container_width=True)

# ── 房价 vs 收入 散点图 ──
st.markdown("---")
st.markdown(f'<h3 style="color:{COLORS["primary"]};">房价 vs 人均可支配收入</h3>', unsafe_allow_html=True)

fig_scatter = px.scatter(
    df, x="per_capita_income", y="avg_price",
    text="city", size="price_income_ratio",
    labels={
        "per_capita_income": "人均可支配收入（元）",
        "avg_price": "二手房均价（元/㎡）",
        "price_income_ratio": "房价收入比",
    },
    color_discrete_sequence=PLOTLY_COLORS,
)
fig_scatter.update_traces(textposition="top center", textfont_size=12)
apply_plotly_style(fig_scatter, 500)
fig_scatter.update_layout(title="收入越高的城市，房价是否越高？")
st.plotly_chart(fig_scatter, use_container_width=True)

# ── 综合数据表 ──
st.markdown("---")
st.markdown(f'<h3 style="color:{COLORS["primary"]};">综合数据表</h3>', unsafe_allow_html=True)

show = df[["city", "avg_price", "per_capita_income", "household_income",
           "total_price_90sqm", "price_income_ratio"]].copy()
show["total_price_90sqm"] = (show["total_price_90sqm"] / 10000).round(1)
show.columns = ["城市", "均价(元/㎡)", "人均可支配收入(元)", "双职工年收入(元)",
                "90㎡总价(万元)", "房价收入比"]
show = show.sort_values("房价收入比", ascending=False)
st.dataframe(show.style.format({
    "均价(元/㎡)": "{:,.0f}",
    "人均可支配收入(元)": "{:,.0f}",
    "双职工年收入(元)": "{:,.0f}",
    "90㎡总价(万元)": "{:.1f}",
    "房价收入比": "{:.1f}",
}), use_container_width=True, hide_index=True)

st.caption(
    "注：均价来源于安居客/房天下/中国房价行情等平台（2026年3月）；"
    "人均可支配收入来源于各城市统计局统计公报（2024年）。"
    "房价收入比的国际警戒线一般为6-9，超过则表示购房压力较大。"
)
