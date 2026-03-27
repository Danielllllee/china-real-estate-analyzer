"""城市横向对比页面 — 仅展示真实均价数据"""
import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from analysis.comparison import compare_cities, compare_districts
from core.styles import inject_global_css, hero_section, apply_plotly_style, PLOTLY_COLORS, COLORS
import yaml

st.set_page_config(page_title="城市对比", page_icon="🌏", layout="wide")
inject_global_css()
hero_section("城市横向对比", "多城市房价对比")

@st.cache_data
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()
all_cities = [v["name"] for v in config["cities"].values()]

selected = st.multiselect("选择对比城市", all_cities, default=all_cities[:4])

if len(selected) < 2:
    st.warning("请至少选择2个城市")
    st.stop()

results = compare_cities(selected)
if not results:
    st.warning("暂无数据")
    st.stop()

df = pd.DataFrame(results)

# 均价对比
fig = px.bar(
    df.sort_values("avg_price", ascending=True),
    y="city", x="avg_price", orientation="h",
    labels={"city": "城市", "avg_price": "均价（元/㎡）"},
    color_discrete_sequence=PLOTLY_COLORS,
    text="avg_price",
)
fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
apply_plotly_style(fig, max(300, len(df) * 45))
fig.update_layout(title="各城市二手房均价排名", yaxis_title="", xaxis_title="均价（元/㎡）")
st.plotly_chart(fig, use_container_width=True)

# 数据表
show_df = df.copy()
show_df["total_price_90sqm"] = (show_df["avg_price"] * 90 / 10000).round(1)
show_df.columns = ["城市", "均价(元/㎡)", "90㎡总价(万元)"]
st.dataframe(show_df, use_container_width=True, hide_index=True)

# 区域详情
st.markdown("---")
st.markdown(f'<h2 style="color:{COLORS["primary"]};">区域明细</h2>', unsafe_allow_html=True)
detail_city = st.selectbox("选择查看", selected, key="detail")
districts = compare_districts(detail_city)

if not districts.empty:
    fig_d = px.bar(
        districts.sort_values("avg_unit_price", ascending=True),
        y="district", x="avg_unit_price", orientation="h",
        labels={"district": "区域", "avg_unit_price": "均价（元/㎡）"},
        color_discrete_sequence=PLOTLY_COLORS,
        text="avg_unit_price",
        title=f"{detail_city} 各区域均价",
    )
    fig_d.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    apply_plotly_style(fig_d, max(300, len(districts) * 40))
    st.plotly_chart(fig_d, use_container_width=True)

    d_df = districts.copy()
    d_df["total_90"] = (d_df["avg_unit_price"] * 90 / 10000).round(1)
    d_df.columns = ["区域", "均价(元/㎡)", "90㎡总价(万元)"]
    st.dataframe(d_df, use_container_width=True, hide_index=True)

st.caption("注：均价数据来源于安居客、房天下、中国房价行情等平台公开的二手房挂牌均价，仅供参考。")
