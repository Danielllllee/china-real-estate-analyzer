"""城市概览页面 — 仅展示经过核实的真实数据"""
import sys
import os
import streamlit as st
import plotly.express as px
import pandas as pd
import yaml

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from analysis.metrics import get_city_overview
from core.styles import (
    inject_global_css,
    hero_section,
    apply_plotly_style,
    PLOTLY_COLORS,
    COLORS,
)

st.set_page_config(page_title="城市概览", page_icon="🏙", layout="wide")

# ============ 全局样式 ============
inject_global_css()

# ============ Hero ============
hero_section("城市概览", "选择城市，一览各区域房价水平")

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
    f'数据来源：安居客/房天下/中国房价行情等平台二手房挂牌均价</p>',
    unsafe_allow_html=True,
)

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

# ============ 数据明细 ============
st.markdown("---")
st.markdown(
    f'<h2 style="color:{COLORS["primary"]};margin-bottom:12px;">数据明细</h2>',
    unsafe_allow_html=True,
)

display_df = overview["districts"][["district", "avg_unit_price"]].copy()
display_df["total_price_90sqm"] = (display_df["avg_unit_price"] * 90 / 10000).round(1)
display_df.columns = ["区域", "均价(元/㎡)", "90㎡总价(万元)"]

st.dataframe(
    display_df.style.format(
        {
            "均价(元/㎡)": "{:,.0f}",
            "90㎡总价(万元)": "{:.1f}",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

st.caption("注：均价数据来源于安居客、房天下、中国房价行情等平台公开的二手房挂牌均价，仅供参考。")
