"""城市横向对比页面"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.comparison import compare_cities, compare_districts
import yaml

st.set_page_config(page_title="城市对比", page_icon="🏙️", layout="wide")
st.title("城市横向对比")

@st.cache_data
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()
all_cities = [v["name"] for v in config["cities"].values()]

selected_cities = st.multiselect("选择要对比的城市", all_cities, default=all_cities[:4])

if len(selected_cities) < 2:
    st.warning("请至少选择2个城市进行对比")
    st.stop()

results = compare_cities(selected_cities)

if not results:
    st.warning("暂无数据")
    st.stop()

df = pd.DataFrame(results)

# 房价对比
st.subheader("各城市均价对比")
fig_price = px.bar(
    df.sort_values("avg_price", ascending=True),
    y="city", x="avg_price",
    orientation="h",
    labels={"city": "城市", "avg_price": "均价（元/㎡）"},
    color="avg_price",
    color_continuous_scale="RdYlGn_r",
)
fig_price.update_layout(height=300, showlegend=False)
st.plotly_chart(fig_price, use_container_width=True)

# 多维度对比
col1, col2 = st.columns(2)

with col1:
    st.subheader("租售比对比")
    fig_rtp = px.bar(
        df.sort_values("avg_rtp", ascending=False),
        x="city", y="avg_rtp",
        labels={"city": "城市", "avg_rtp": "租售比（年）"},
        color="avg_rtp",
        color_continuous_scale="RdYlGn",
        title="租售比（越高越有投资价值）",
    )
    fig_rtp.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig_rtp, use_container_width=True)

with col2:
    if "price_to_income" in df.columns:
        st.subheader("房价收入比")
        fig_pti = px.bar(
            df.sort_values("price_to_income", ascending=True),
            x="city", y="price_to_income",
            labels={"city": "城市", "price_to_income": "房价收入比"},
            color="price_to_income",
            color_continuous_scale="RdYlGn_r",
            title="房价收入比（越低越可负担）",
        )
        fig_pti.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_pti, use_container_width=True)

# 综合数据表
st.subheader("综合数据对比")
display_cols = {
    "city": "城市",
    "avg_price": "均价(元/㎡)",
    "avg_rent": "月租金(元/㎡)",
    "avg_rtp": "租售比(年)",
    "total_txn": "月成交量",
    "avg_cycle": "成交周期(天)",
}
if "population" in df.columns:
    display_cols["population"] = "人口(万)"
if "gdp" in df.columns:
    display_cols["gdp"] = "GDP(亿元)"
if "disposable_income" in df.columns:
    display_cols["disposable_income"] = "人均可支配收入"
if "price_to_income" in df.columns:
    display_cols["price_to_income"] = "房价收入比"

display_df = df[[c for c in display_cols.keys() if c in df.columns]].copy()
display_df.columns = [display_cols[c] for c in display_df.columns]

# 格式化数值
for col in display_df.columns:
    if display_df[col].dtype in ["float64", "float32"]:
        display_df[col] = display_df[col].round(2)

st.dataframe(display_df, use_container_width=True, hide_index=True)

# 各城市区域详情
st.markdown("---")
st.subheader("选定城市的区域分析")
detail_city = st.selectbox("查看城市区域详情", selected_cities)

districts = compare_districts(detail_city)
if not districts.empty:
    districts_display = districts.copy()
    districts_display.columns = ["区域", "均价(元/㎡)", "月租金(元/㎡)", "租售比(年)",
                                  "月成交量", "在售挂牌", "成交周期(天)"]
    st.dataframe(districts_display, use_container_width=True, hide_index=True)

    # 性价比散点图
    fig_scatter = px.scatter(
        districts, x="avg_unit_price", y="rent_to_price_ratio",
        text="district", size="transaction_count",
        labels={"avg_unit_price": "均价（元/㎡）", "rent_to_price_ratio": "租售比",
                "transaction_count": "成交量"},
        title=f"{detail_city} 各区域性价比分布（右上角=高价高租售比，左上角=低价高租售比=性价比最优）",
    )
    fig_scatter.update_traces(textposition="top center")
    fig_scatter.update_layout(height=450)
    st.plotly_chart(fig_scatter, use_container_width=True)
