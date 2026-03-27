"""区域分析页面 — 展示真实均价+租金数据"""
import sys
import os
import streamlit as st
import pandas as pd
import yaml

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.database import query_df
from core.styles import (
    inject_global_css, hero_section, metric_card,
    get_district_names, COLORS,
)

st.set_page_config(page_title="区域分析", page_icon="📊", layout="wide")
inject_global_css()

# ── 配置加载 ──
@st.cache_data
def load_config():
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config.yaml",
    )
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

# ── 城市 / 区域选择 ──
col_sel1, col_sel2, _ = st.columns([1, 1, 2])
city_names = {k: v["name"] for k, v in config["cities"].items()}
with col_sel1:
    selected_city = st.selectbox("选择城市", list(city_names.values()), label_visibility="collapsed")
city_key = [k for k, v in config["cities"].items() if v["name"] == selected_city][0]
district_pairs = get_district_names(config["cities"][city_key])
district_display = [dp[0] for dp in district_pairs]
district_actual = [dp[1] for dp in district_pairs]
with col_sel2:
    sel_idx = st.selectbox("选择区域", range(len(district_display)),
                           format_func=lambda i: district_display[i], label_visibility="collapsed")
    selected_district = district_actual[sel_idx]

# ── 获取数据 ──
latest = query_df("""
    SELECT avg_unit_price, avg_rent_per_sqm, rent_to_price_ratio
    FROM district_stats
    WHERE city = ? AND district = ?
    ORDER BY month DESC LIMIT 1
""", [selected_city, selected_district])

if latest.empty or latest.iloc[0]["avg_unit_price"] is None:
    st.warning("暂无该区域数据")
    st.stop()

row = latest.iloc[0]
avg_price = row["avg_unit_price"]
rent = row["avg_rent_per_sqm"]
rent_ratio = row["rent_to_price_ratio"]

# ── 展示 ──
hero_section(
    f"{selected_city} · {selected_district}",
    f"二手房挂牌均价及租金数据（来源：安居客/房天下/中国房价行情/21经济网等）",
)

# 指标卡片
cols = [c for c in st.columns(4)]
with cols[0]:
    st.markdown(metric_card("🏠", "二手房均价", f"{avg_price:,.0f} 元/㎡"), unsafe_allow_html=True)
with cols[1]:
    total_90 = avg_price * 90 / 10000
    st.markdown(metric_card("📐", "90㎡总价", f"{total_90:.0f} 万元"), unsafe_allow_html=True)
with cols[2]:
    if rent is not None:
        st.markdown(metric_card("🏘", "月租金", f"{rent:.0f} 元/㎡/月"), unsafe_allow_html=True)
    else:
        total_120 = avg_price * 120 / 10000
        st.markdown(metric_card("🏗", "120㎡总价", f"{total_120:.0f} 万元"), unsafe_allow_html=True)
with cols[3]:
    if rent is not None:
        annual_yield = rent * 12 / avg_price * 100
        st.markdown(metric_card("📈", "年租金回报率", f"{annual_yield:.2f}%"), unsafe_allow_html=True)
    else:
        total_120 = avg_price * 120 / 10000
        st.markdown(metric_card("🏗", "120㎡总价", f"{total_120:.0f} 万元"), unsafe_allow_html=True)

# ── 租金估值分析（如果有租金数据）──
if rent is not None:
    st.markdown("---")
    st.markdown(f'<h3 style="color:{COLORS["primary"]};">租金回报分析</h3>', unsafe_allow_html=True)

    annual_rent_90 = rent * 12 * 90
    total_price_90 = avg_price * 90
    payback_years = total_price_90 / annual_rent_90 if annual_rent_90 > 0 else 0

    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        st.markdown(metric_card("💵", "90㎡年租金收入", f"{annual_rent_90/10000:.1f} 万元"), unsafe_allow_html=True)
    with rc2:
        st.markdown(metric_card("⏳", "静态回本年限", f"{payback_years:.0f} 年"), unsafe_allow_html=True)
    with rc3:
        monthly_rent_90 = rent * 90
        st.markdown(metric_card("🏠", "90㎡月租金", f"{monthly_rent_90:,.0f} 元"), unsafe_allow_html=True)

# ── 同城对比 ──
st.markdown("---")
st.markdown(f'<h3 style="color:{COLORS["primary"]};">同城各区域均价对比</h3>', unsafe_allow_html=True)

all_districts = query_df("""
    SELECT district, avg_unit_price, avg_rent_per_sqm FROM district_stats
    WHERE city = ? AND month = (SELECT MAX(month) FROM district_stats WHERE city = ?)
    ORDER BY avg_unit_price DESC
""", [selected_city, selected_city])

if not all_districts.empty:
    import plotly.express as px
    from core.styles import apply_plotly_style, PLOTLY_COLORS

    fig = px.bar(
        all_districts.sort_values("avg_unit_price", ascending=True),
        y="district", x="avg_unit_price", orientation="h",
        labels={"district": "区域", "avg_unit_price": "均价（元/㎡）"},
        color_discrete_sequence=PLOTLY_COLORS,
        text="avg_unit_price",
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    apply_plotly_style(fig, max(360, len(all_districts) * 40))
    fig.update_layout(yaxis_title="", xaxis_title="均价（元/㎡）")

    # 高亮当前选中的区域
    colors = [COLORS["accent"] if d == selected_district else PLOTLY_COLORS[0]
              for d in all_districts.sort_values("avg_unit_price", ascending=True)["district"]]
    fig.update_traces(marker_color=colors)

    st.plotly_chart(fig, use_container_width=True)

st.caption(
    "注：均价来源于安居客/房天下/中国房价行情等平台；"
    "租金来源于21经济网/中指云/广州房协等机构报告。所有数据仅供参考。"
)
