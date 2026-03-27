"""估值计算器 — 基于真实租金数据的租金收益率法估值"""
import streamlit as st
import sys, os
import yaml

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.database import query_df
from core.styles import inject_global_css, hero_section, metric_card, get_district_names, COLORS
from models.rental_yield import get_area_rental_data, estimate_by_rental_yield, evaluate_current_price

st.set_page_config(page_title="估值计算器", page_icon="🧮", layout="wide")
inject_global_css()
hero_section("估值计算器", "基于真实租金数据的租金收益率法估值")

# ── 配置 ──
@st.cache_data
def load_config():
    config_path = os.path.join(_ROOT, "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()
city_names = {k: v["name"] for k, v in config["cities"].items()}

# ── 选择城市/区域 ──
c1, c2, _ = st.columns([1, 1, 2])
with c1:
    selected_city = st.selectbox("选择城市", list(city_names.values()), label_visibility="collapsed")
city_key = [k for k, v in config["cities"].items() if v["name"] == selected_city][0]
district_pairs = get_district_names(config["cities"][city_key])
with c2:
    sel_idx = st.selectbox("选择区域", range(len(district_pairs)),
                           format_func=lambda i: district_pairs[i][0], label_visibility="collapsed")
    selected_district = district_pairs[sel_idx][1]

# ── 获取数据 ──
rental = get_area_rental_data(selected_city, selected_district)
price_data = query_df("""
    SELECT avg_unit_price FROM district_stats
    WHERE city = ? AND district = ? ORDER BY month DESC LIMIT 1
""", [selected_city, selected_district])

if price_data.empty:
    st.warning("暂无该区域房价数据")
    st.stop()

current_price = price_data.iloc[0]["avg_unit_price"]

if rental is None:
    st.info(f"暂无 {selected_city}·{selected_district} 的租金数据，无法进行租金收益率法估值。")
    st.markdown(f"当前二手房均价：**{current_price:,.0f} 元/㎡**")
    st.stop()

# ── 参数调整 ──
st.markdown("---")
st.markdown(f'<h3 style="color:{COLORS["primary"]};">估值参数</h3>', unsafe_allow_html=True)

p1, p2, p3 = st.columns(3)
with p1:
    risk_free = st.slider("无风险利率（10年期国债）", 0.01, 0.05, 0.025, 0.005, format="%.3f")
with p2:
    risk_premium = st.slider("房产风险溢价", 0.01, 0.06, 0.025, 0.005, format="%.3f")
with p3:
    vacancy = st.slider("空置率", 0.0, 0.15, 0.05, 0.01, format="%.2f")

# ── 计算估值 ──
monthly_rent = rental["avg_rent_per_sqm"]
annual_rent = monthly_rent * 12

valuation = estimate_by_rental_yield(
    annual_rent_per_sqm=annual_rent,
    risk_free_rate=risk_free,
    risk_premium=risk_premium,
    vacancy_rate=vacancy,
)

evaluation = evaluate_current_price(current_price, valuation)

# ── 展示结果 ──
st.markdown("---")
st.markdown(f'<h3 style="color:{COLORS["primary"]};">估值结果</h3>', unsafe_allow_html=True)

v1, v2, v3, v4 = st.columns(4)
with v1:
    st.markdown(metric_card("🏠", "当前均价", f"{current_price:,.0f} 元/㎡"), unsafe_allow_html=True)
with v2:
    st.markdown(metric_card("📊", "合理估值", f"{valuation['fair_value_per_sqm']:,.0f} 元/㎡"), unsafe_allow_html=True)
with v3:
    st.markdown(metric_card("📈", "偏离度", evaluation["deviation_pct"]), unsafe_allow_html=True)
with v4:
    st.markdown(metric_card("🎯", "评估", evaluation["assessment"]), unsafe_allow_html=True)

# 详情
st.markdown("---")
st.markdown(f'<h3 style="color:{COLORS["primary"]};">详细数据</h3>', unsafe_allow_html=True)

d1, d2 = st.columns(2)
with d1:
    st.markdown("**租金数据**")
    st.write(f"- 月租金均价：{monthly_rent:.0f} 元/㎡/月")
    st.write(f"- 年租金：{annual_rent:.0f} 元/㎡/年")
    st.write(f"- 实际租金回报率：{evaluation['actual_yield_pct']}")
    st.write(f"- 90㎡年租金收入：{annual_rent * 90 / 10000:.1f} 万元")

with d2:
    st.markdown("**估值区间**")
    st.write(f"- 保守估值：{valuation['conservative_value']:,.0f} 元/㎡")
    st.write(f"- 中性估值：{valuation['fair_value_per_sqm']:,.0f} 元/㎡")
    st.write(f"- 乐观估值：{valuation['optimistic_value']:,.0f} 元/㎡")
    st.write(f"- 资本化率(Cap Rate)：{valuation['cap_rate']*100:.1f}%")

st.caption(
    "注：租金收益率法是房产估值的基本方法之一。合理价格 = 净年租金 / 资本化率。"
    "资本化率 = 无风险利率 + 房产风险溢价。该方法假设房产价值取决于其产生的现金流。"
    "租金数据来源于21经济网、中指云等机构报告，仅供参考。"
)
