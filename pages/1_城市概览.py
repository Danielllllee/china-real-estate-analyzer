"""城市概览页面 — 展示经过核实的真实数据（均价+租金+宏观）"""
import sys
import os
import streamlit as st
import plotly.express as px
import pandas as pd
import yaml

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from analysis.metrics import get_city_overview, get_city_macro, calculate_affordability
from core.styles import (
    inject_global_css,
    hero_section,
    apply_plotly_style,
    metric_card,
    PLOTLY_COLORS,
    COLORS,
)

st.set_page_config(page_title="城市概览", page_icon="🏙", layout="wide")

# ============ 全局样式 ============
inject_global_css()

# ============ Hero ============
hero_section("城市概览", "选择城市，一览各区域房价与租金水平")

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
    f'数据截至 <b>{overview["latest_month"]}</b>　|　'
    f'数据来源：安居客/房天下/中国房价行情等平台</p>',
    unsafe_allow_html=True,
)

# ============ 宏观数据概览 ============
macro = get_city_macro(selected_city)
affordability = calculate_affordability(selected_city)

if macro:
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.markdown(metric_card("💰", "GDP", f"{macro['gdp']:,.0f} 亿元"), unsafe_allow_html=True)
    with mc2:
        st.markdown(metric_card("👥", "常住人口", f"{macro['population']:.0f} 万人"), unsafe_allow_html=True)
    with mc3:
        st.markdown(metric_card("📊", "人均可支配收入", f"{macro['per_capita_income']:,.0f} 元"), unsafe_allow_html=True)
    with mc4:
        if affordability:
            st.markdown(metric_card("🏠", "房价收入比", f"{affordability['price_income_ratio']:.1f}"), unsafe_allow_html=True)
        else:
            st.markdown(metric_card("📅", "数据年份", macro['data_year']), unsafe_allow_html=True)
    st.caption(f"宏观数据来源：各城市统计局统计公报（{macro['data_year']}年）")

# ============ 均价排名图 ============
districts = overview["districts"].sort_values("avg_unit_price", ascending=True)

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
apply_plotly_style(fig_price, height=max(360, len(districts) * 45))
fig_price.update_layout(
    title=dict(text="各区域二手房挂牌均价", font=dict(size=16)),
    yaxis=dict(title=""),
    xaxis=dict(title="均价（元/㎡）"),
)
st.plotly_chart(fig_price, use_container_width=True)

# ============ 租金排名图 ============
has_rent = districts["avg_rent_per_sqm"].notna().any()
if has_rent:
    rent_df = districts[districts["avg_rent_per_sqm"].notna()].sort_values("avg_rent_per_sqm", ascending=True)
    fig_rent = px.bar(
        rent_df,
        y="district",
        x="avg_rent_per_sqm",
        orientation="h",
        labels={"district": "区域", "avg_rent_per_sqm": "月租金（元/㎡/月）"},
        color_discrete_sequence=["#10b981"],
        text="avg_rent_per_sqm",
    )
    fig_rent.update_traces(texttemplate="%{text:.0f}", textposition="outside")
    apply_plotly_style(fig_rent, height=max(360, len(rent_df) * 45))
    fig_rent.update_layout(
        title=dict(text="各区域住宅月租金均价", font=dict(size=16)),
        yaxis=dict(title=""),
        xaxis=dict(title="月租金（元/㎡/月）"),
    )
    st.plotly_chart(fig_rent, use_container_width=True)

# ============ 数据明细 ============
st.markdown("---")
st.markdown(
    f'<h2 style="color:{COLORS["primary"]};margin-bottom:12px;">数据明细</h2>',
    unsafe_allow_html=True,
)

display_df = overview["districts"][["district", "avg_unit_price"]].copy()
display_df["total_price_90sqm"] = (display_df["avg_unit_price"] * 90 / 10000).round(1)

# 添加租金和收益率列
if has_rent:
    display_df["rent"] = overview["districts"]["avg_rent_per_sqm"]
    display_df["annual_yield"] = (overview["districts"]["avg_rent_per_sqm"] * 12 / overview["districts"]["avg_unit_price"] * 100).round(2)
    display_df.columns = ["区域", "均价(元/㎡)", "90㎡总价(万元)", "月租金(元/㎡/月)", "年租金回报率(%)"]
    fmt = {
        "均价(元/㎡)": "{:,.0f}",
        "90㎡总价(万元)": "{:.1f}",
        "月租金(元/㎡/月)": "{:.0f}",
        "年租金回报率(%)": "{:.2f}",
    }
else:
    display_df.columns = ["区域", "均价(元/㎡)", "90㎡总价(万元)"]
    fmt = {
        "均价(元/㎡)": "{:,.0f}",
        "90㎡总价(万元)": "{:.1f}",
    }

st.dataframe(
    display_df.style.format(fmt),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "注：均价数据来源于安居客、房天下、中国房价行情等平台公开的二手房挂牌均价；"
    "租金数据来源于21经济网、中指云、广州房协等机构的市场分析报告。仅供参考。"
)
