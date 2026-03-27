"""收益率分析 — 基于真实租金数据的各城市租金回报率对比"""
import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os
import yaml

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.database import query_df
from core.styles import inject_global_css, hero_section, apply_plotly_style, metric_card, PLOTLY_COLORS, COLORS

st.set_page_config(page_title="收益率分析", page_icon="📈", layout="wide")
inject_global_css()
hero_section("租金收益率分析", "各城市各区域年租金回报率对比")

# ── 获取所有有租金数据的区域 ──
data = query_df("""
    SELECT city, district, avg_unit_price, avg_rent_per_sqm,
           avg_rent_per_sqm * 12 / avg_unit_price * 100 as annual_yield,
           avg_unit_price * 90 / 10000 as total_90
    FROM district_stats
    WHERE avg_rent_per_sqm IS NOT NULL
    AND month = (SELECT MAX(month) FROM district_stats)
    ORDER BY annual_yield DESC
""")

if data.empty:
    st.warning("暂无租金数据")
    st.stop()

# ── 全国收益率排行 ──
st.markdown(f'<h3 style="color:{COLORS["primary"]};">全国区域租金回报率排行</h3>', unsafe_allow_html=True)

# 计算城市级别的平均收益率
city_yield = data.groupby("city").agg(
    avg_yield=("annual_yield", "mean"),
    avg_price=("avg_unit_price", "mean"),
    avg_rent=("avg_rent_per_sqm", "mean"),
).reset_index().sort_values("avg_yield", ascending=False)

fig_city = px.bar(
    city_yield.sort_values("avg_yield", ascending=True),
    y="city", x="avg_yield", orientation="h",
    labels={"city": "城市", "avg_yield": "平均年租金回报率(%)"},
    color_discrete_sequence=["#10b981"],
    text="avg_yield",
)
fig_city.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
apply_plotly_style(fig_city, max(400, len(city_yield) * 35))
fig_city.update_layout(
    title="各城市平均年租金回报率",
    yaxis_title="",
    xaxis_title="年租金回报率(%)",
)
st.plotly_chart(fig_city, use_container_width=True)

# ── 城市级别数据表 ──
show_city = city_yield.copy()
show_city["avg_yield"] = show_city["avg_yield"].round(2)
show_city["avg_price"] = show_city["avg_price"].round(0)
show_city["avg_rent"] = show_city["avg_rent"].round(1)
show_city.columns = ["城市", "平均年回报率(%)", "平均均价(元/㎡)", "平均月租金(元/㎡/月)"]
st.dataframe(show_city, use_container_width=True, hide_index=True)

# ── 选择城市查看区域详情 ──
st.markdown("---")
st.markdown(f'<h3 style="color:{COLORS["primary"]};">区域收益率详情</h3>', unsafe_allow_html=True)

cities = sorted(data["city"].unique())
sel_city = st.selectbox("选择城市查看", cities)

city_data = data[data["city"] == sel_city].sort_values("annual_yield", ascending=True)

fig_dist = px.bar(
    city_data,
    y="district", x="annual_yield", orientation="h",
    labels={"district": "区域", "annual_yield": "年租金回报率(%)"},
    color_discrete_sequence=["#10b981"],
    text="annual_yield",
)
fig_dist.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
apply_plotly_style(fig_dist, max(300, len(city_data) * 40))
fig_dist.update_layout(
    title=f"{sel_city} 各区域年租金回报率",
    yaxis_title="",
    xaxis_title="年租金回报率(%)",
)
st.plotly_chart(fig_dist, use_container_width=True)

# 详细数据表
detail = city_data[["district", "avg_unit_price", "avg_rent_per_sqm", "annual_yield", "total_90"]].copy()
detail["annual_yield"] = detail["annual_yield"].round(2)
detail["total_90"] = detail["total_90"].round(1)
detail["payback_years"] = (detail["avg_unit_price"] / (detail["avg_rent_per_sqm"] * 12)).round(0)
detail.columns = ["区域", "均价(元/㎡)", "月租金(元/㎡/月)", "年回报率(%)", "90㎡总价(万元)", "静态回本年限"]
detail = detail.sort_values("年回报率(%)", ascending=False)
st.dataframe(detail, use_container_width=True, hide_index=True)

st.caption(
    "注：年租金回报率 = 月租金 × 12 / 房价 × 100%。静态回本年限 = 房价 / 年租金。"
    "均价来源于安居客/房天下/中国房价行情等平台；租金来源于21经济网/中指云/广州房协等机构报告。"
    "实际收益还需考虑空置率、维修成本、税费等因素。"
)
