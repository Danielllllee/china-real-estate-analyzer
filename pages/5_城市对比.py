"""城市横向对比页面 — 展示真实均价+租金+宏观数据"""
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
hero_section("城市横向对比", "多城市房价、租金、经济数据对比")

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

# ── 均价对比 ──
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

# ── 租金回报率对比 ──
if "annual_yield" in df.columns:
    yield_df = df[df["annual_yield"].notna()].sort_values("annual_yield", ascending=True)
    if not yield_df.empty:
        fig_yield = px.bar(
            yield_df,
            y="city", x="annual_yield", orientation="h",
            labels={"city": "城市", "annual_yield": "年租金回报率(%)"},
            color_discrete_sequence=["#10b981"],
            text="annual_yield",
        )
        fig_yield.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        apply_plotly_style(fig_yield, max(300, len(yield_df) * 45))
        fig_yield.update_layout(title="各城市平均年租金回报率", yaxis_title="", xaxis_title="年租金回报率(%)")
        st.plotly_chart(fig_yield, use_container_width=True)

# ── 综合数据表 ──
show_df = df.copy()
show_df["total_price_90sqm"] = (show_df["avg_price"] * 90 / 10000).round(1)
cols_rename = {"city": "城市", "avg_price": "均价(元/㎡)", "total_price_90sqm": "90㎡总价(万元)"}
if "avg_rent" in show_df.columns:
    cols_rename["avg_rent"] = "月租金(元/㎡/月)"
if "annual_yield" in show_df.columns:
    cols_rename["annual_yield"] = "年回报率(%)"
if "gdp" in show_df.columns:
    cols_rename["gdp"] = "GDP(亿元)"
if "population" in show_df.columns:
    cols_rename["population"] = "人口(万人)"
if "per_capita_income" in show_df.columns:
    cols_rename["per_capita_income"] = "人均可支配收入(元)"

display_cols = [c for c in cols_rename.keys() if c in show_df.columns]
show_df = show_df[display_cols].rename(columns=cols_rename)
st.dataframe(show_df, use_container_width=True, hide_index=True)

# ── 区域详情 ──
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

    d_df = districts[["district", "avg_unit_price"]].copy()
    d_df["total_90"] = (d_df["avg_unit_price"] * 90 / 10000).round(1)
    if "avg_rent_per_sqm" in districts.columns:
        d_df["rent"] = districts["avg_rent_per_sqm"]
        d_df["yield"] = (districts["avg_rent_per_sqm"] * 12 / districts["avg_unit_price"] * 100).round(2)
        d_df.columns = ["区域", "均价(元/㎡)", "90㎡总价(万元)", "月租金(元/㎡/月)", "年回报率(%)"]
    else:
        d_df.columns = ["区域", "均价(元/㎡)", "90㎡总价(万元)"]
    st.dataframe(d_df, use_container_width=True, hide_index=True)

st.caption(
    "注：均价来源于安居客/房天下/中国房价行情等平台；租金来源于21经济网/中指云等机构报告；"
    "宏观数据来源于各城市统计局统计公报。所有数据仅供参考。"
)
