"""区域分析页面 — 仅展示真实数据"""
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
    SELECT avg_unit_price FROM district_stats
    WHERE city = ? AND district = ?
    ORDER BY month DESC LIMIT 1
""", [selected_city, selected_district])

if latest.empty or latest.iloc[0]["avg_unit_price"] is None:
    st.warning("暂无该区域数据")
    st.stop()

avg_price = latest.iloc[0]["avg_unit_price"]

# ── 展示 ──
hero_section(
    f"{selected_city} · {selected_district}",
    f"二手房挂牌均价数据（来源：安居客/房天下/中国房价行情等平台）",
)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(metric_card("🏠", "二手房均价", f"{avg_price:,.0f} 元/㎡"), unsafe_allow_html=True)
with c2:
    total_90 = avg_price * 90 / 10000
    st.markdown(metric_card("📐", "90㎡总价", f"{total_90:.0f} 万元"), unsafe_allow_html=True)
with c3:
    total_120 = avg_price * 120 / 10000
    st.markdown(metric_card("🏗", "120㎡总价", f"{total_120:.0f} 万元"), unsafe_allow_html=True)

# ── 同城对比 ──
st.markdown("---")
st.markdown(f'<h3 style="color:{COLORS["primary"]};">同城各区域均价对比</h3>', unsafe_allow_html=True)

all_districts = query_df("""
    SELECT district, avg_unit_price FROM district_stats
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

st.caption("注：当前仅展示经过核实的区域均价数据。租金、成交量、历史走势等数据尚未接入真实数据源。")
