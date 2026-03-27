"""城市横向对比页面 — Premium UI"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from analysis.comparison import compare_cities, compare_districts
from utils.styles import inject_global_css, hero_section, metric_card, apply_plotly_style, PLOTLY_COLORS, COLORS
import yaml

st.set_page_config(page_title="城市对比", page_icon="🌏", layout="wide")
inject_global_css()
hero_section("城市横向对比", "多城市核心指标对比，找到最具投资价值的城市")

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

# 三项核心对比
tab1, tab2, tab3 = st.tabs(["房价对比", "投资价值", "综合数据"])

with tab1:
    fig = px.bar(
        df.sort_values("avg_price", ascending=True),
        y="city", x="avg_price", orientation="h",
        labels={"city": "城市", "avg_price": "均价（元/㎡）"},
        color_discrete_sequence=PLOTLY_COLORS,
        text="avg_price",
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    apply_plotly_style(fig, max(300, len(df) * 45))
    fig.update_layout(title="各城市均价排名", yaxis_title="", xaxis_title="均价（元/㎡）")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        fig_rtp = px.bar(
            df.sort_values("avg_rtp", ascending=False),
            x="city", y="avg_rtp",
            labels={"city": "", "avg_rtp": "租售比（年）"},
            color_discrete_sequence=[COLORS["success"]],
            text="avg_rtp", title="租售比（越高越有投资价值）",
        )
        fig_rtp.update_traces(texttemplate="%{text:.4f}", textposition="outside")
        apply_plotly_style(fig_rtp, 380)
        st.plotly_chart(fig_rtp, use_container_width=True)

    with col2:
        if "price_to_income" in df.columns:
            fig_pti = px.bar(
                df.sort_values("price_to_income"),
                x="city", y="price_to_income",
                labels={"city": "", "price_to_income": "房价收入比"},
                color_discrete_sequence=[COLORS["accent"]],
                text="price_to_income", title="房价收入比（越低越可负担）",
            )
            fig_pti.update_traces(texttemplate="%{text:.1f}", textposition="outside")
            apply_plotly_style(fig_pti, 380)
            st.plotly_chart(fig_pti, use_container_width=True)

with tab3:
    cols_map = {
        "city": "城市", "avg_price": "均价(元/㎡)", "avg_rent": "月租金(元/㎡)",
        "avg_rtp": "租售比", "total_txn": "月成交量", "avg_cycle": "成交周期(天)",
    }
    if "population" in df.columns:
        cols_map["population"] = "人口(万)"
    if "gdp" in df.columns:
        cols_map["gdp"] = "GDP(亿)"
    if "disposable_income" in df.columns:
        cols_map["disposable_income"] = "人均收入"
    if "price_to_income" in df.columns:
        cols_map["price_to_income"] = "房价收入比"

    show_df = df[[c for c in cols_map if c in df.columns]].copy()
    show_df.columns = [cols_map[c] for c in show_df.columns]
    for col in show_df.select_dtypes("float"):
        show_df[col] = show_df[col].round(2)
    st.dataframe(show_df, use_container_width=True, hide_index=True)

# 区域详情
st.markdown("---")
st.markdown(f'<h2 style="color:{COLORS["primary"]};">区域分析</h2>', unsafe_allow_html=True)
detail_city = st.selectbox("选择查看", selected, key="detail")
districts = compare_districts(detail_city)

if not districts.empty:
    fig_scatter = px.scatter(
        districts, x="avg_unit_price", y="rent_to_price_ratio",
        text="district", size="transaction_count",
        labels={"avg_unit_price": "均价（元/㎡）", "rent_to_price_ratio": "租售比", "transaction_count": "成交量"},
        title=f"{detail_city} 各区域性价比（左上角=性价比最优）",
        color_discrete_sequence=PLOTLY_COLORS,
    )
    fig_scatter.update_traces(textposition="top center", textfont_size=11)
    apply_plotly_style(fig_scatter, 450)
    st.plotly_chart(fig_scatter, use_container_width=True)

    d_df = districts.copy()
    d_df.columns = ["区域", "均价(元/㎡)", "月租金(元/㎡)", "租售比", "月成交量", "在售挂牌", "成交周期(天)"]
    st.dataframe(d_df, use_container_width=True, hide_index=True)
