"""单套房产估值计算器 — Premium UI"""
import streamlit as st
import plotly.graph_objects as go
import sys, os
# 确保项目根目录在 sys.path 中（兼容 Streamlit Cloud）
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from models.composite import composite_valuation
from utils.styles import inject_global_css, hero_section, metric_card, apply_plotly_style, get_district_names, PLOTLY_COLORS, COLORS
import yaml

st.set_page_config(page_title="估值计算器", page_icon="🧮", layout="wide")
inject_global_css()

@st.cache_data
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

hero_section("估值计算器", "输入房产信息，四大模型综合估值，精准定价")

# 输入表单卡片
st.markdown('<div class="content-card">', unsafe_allow_html=True)
st.markdown("#### 房产基本信息")
col1, col2, col3 = st.columns(3)

with col1:
    city_names = {k: v["name"] for k, v in config["cities"].items()}
    selected_city = st.selectbox("城市", list(city_names.values()))
    city_key = [k for k, v in config["cities"].items() if v["name"] == selected_city][0]
    dp = get_district_names(config["cities"][city_key])
    sel_d = st.selectbox("区域", range(len(dp)), format_func=lambda i: dp[i][0])
    selected_district = dp[sel_d][1]

with col2:
    area = st.number_input("面积（㎡）", min_value=20, max_value=500, value=90)
    building_age = st.number_input("房龄（年）", min_value=0, max_value=50, value=10)

with col3:
    floor_level = st.selectbox("楼层", ["low", "mid", "mid_high", "high"],
                                format_func=lambda x: {"low": "低楼层(1-6)", "mid": "中楼层(7-15)",
                                                        "mid_high": "中高(16-25)", "high": "高楼层(26+)"}[x])
    decoration = st.selectbox("装修", ["rough", "simple", "fine", "luxury"],
                               format_func=lambda x: {"rough": "毛坯", "simple": "简装",
                                                       "fine": "精装", "luxury": "豪装"}[x])

col4, col5, _ = st.columns(3)
with col4:
    orientation = st.selectbox("朝向", ["south", "south_north", "east", "west", "north"],
                                format_func=lambda x: {"south": "南", "south_north": "南北通透",
                                                        "east": "东", "west": "西", "north": "北"}[x])
with col5:
    current_price = st.number_input("当前挂牌价（元/㎡，选填，0=不对比）", min_value=0, value=0)

calc_btn = st.button("开始估值", type="primary", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

if calc_btn:
    with st.spinner("四大模型计算中..."):
        result = composite_valuation(
            city=selected_city, district=selected_district,
            area=area, floor_level=floor_level, decoration=decoration,
            building_age=building_age, orientation=orientation,
            current_price_per_sqm=current_price if current_price > 0 else None,
        )

    if "error" in result:
        st.error(result["error"])
        st.stop()

    comp = result["composite"]

    # 结果卡片
    st.markdown("### 综合估值结果")
    cols = st.columns(3)
    with cols[0]:
        st.markdown(metric_card("🛡", "保守估值", f"{comp['conservative_value']:,} 元/㎡",
                                 f"总价 {comp['conservative_total_price']} 万", "warning"),
                    unsafe_allow_html=True)
    with cols[1]:
        st.markdown(metric_card("🎯", "中性估值", f"{comp['fair_value_per_sqm']:,} 元/㎡",
                                 f"总价 {comp['fair_total_price']} 万", "info"),
                    unsafe_allow_html=True)
    with cols[2]:
        st.markdown(metric_card("🚀", "乐观估值", f"{comp['optimistic_value']:,} 元/㎡",
                                 f"总价 {comp['optimistic_total_price']} 万", "success"),
                    unsafe_allow_html=True)

    # 偏离度评估
    if "composite_assessment" in result:
        ca = result["composite_assessment"]
        dev = float(ca["deviation_pct"].strip("%+"))
        color = COLORS["success"] if dev < 0 else COLORS["danger"]
        st.markdown(f"""
        <div class="content-card" style="border-left:4px solid {color};">
            <div style="display:flex;align-items:center;justify-content:space-between;">
                <div>
                    <div style="font-size:14px;color:#94a3b8;">当前挂牌价 vs 综合估值</div>
                    <div style="font-size:24px;font-weight:700;color:{color};margin:8px 0;">{ca['deviation_pct']}</div>
                </div>
                <div style="font-size:15px;color:#2c3e50;max-width:60%;">{ca['recommendation']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 各模型对比图
    st.markdown("### 各模型估值对比")
    models = result["models"]
    model_names, fair_vals, cons_vals, opt_vals = [], [], [], []

    for key, model in models.items():
        if "fair_value_per_sqm" in model:
            model_names.append(model["model_name"])
            fair_vals.append(model["fair_value_per_sqm"])
            cons_vals.append(model["conservative_value"])
            opt_vals.append(model["optimistic_value"])

    if model_names:
        fig = go.Figure()
        fig.add_trace(go.Bar(name="保守", x=model_names, y=cons_vals, marker_color=COLORS["warning"]))
        fig.add_trace(go.Bar(name="中性", x=model_names, y=fair_vals, marker_color=COLORS["primary"]))
        fig.add_trace(go.Bar(name="乐观", x=model_names, y=opt_vals, marker_color=COLORS["success"]))
        if current_price > 0:
            fig.add_hline(y=current_price, line_dash="dash", line_color=COLORS["accent"],
                          annotation_text=f"挂牌价 {current_price:,}")
        fig.update_layout(barmode="group", yaxis_title="元/㎡")
        apply_plotly_style(fig, 420)
        st.plotly_chart(fig, use_container_width=True)

    # 模型详情 tabs
    st.markdown("### 模型参数详情")
    model_tabs = st.tabs([m["model_name"] for m in models.values() if "fair_value_per_sqm" in m])
    for tab, (key, model) in zip(model_tabs, [(k, v) for k, v in models.items() if "fair_value_per_sqm" in v]):
        with tab:
            if key == "rental_yield":
                c1, c2, c3 = st.columns(3)
                c1.metric("年毛租金", f"{model.get('gross_annual_rent_per_sqm', 'N/A')} 元/㎡")
                c2.metric("资本化率", f"{model.get('cap_rate', 0)*100:.2f}%")
                c3.metric("无风险利率", f"{model.get('risk_free_rate', 0)*100:.2f}%")
            elif key == "comparable":
                c1, c2, c3 = st.columns(3)
                c1.metric("可比样本数", model.get("sample_count", "N/A"))
                c2.metric("价格区间", f"{model.get('price_range', ['N/A'])[0]:,} - {model.get('price_range', ['','N/A'])[1]:,}")
                c3.metric("标准差", f"{model.get('std_dev', 'N/A'):,}")
            elif key == "dcf":
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("折现率", f"{model.get('discount_rate', 0)*100:.2f}%")
                c2.metric("租金增长率", f"{model.get('rent_growth_rate', 0)*100:.2f}%")
                c3.metric("终值占比", f"{model.get('terminal_share', 'N/A')}%")
                c4.metric("预测期", f"{model.get('projection_years', 'N/A')} 年")
            elif key == "cost_approach":
                c1, c2, c3 = st.columns(3)
                c1.metric("土地楼面价", f"{model.get('land_cost', 'N/A'):,} 元/㎡")
                c2.metric("建造成本", f"{model.get('construction_cost', 'N/A'):,} 元/㎡")
                c3.metric("开发商利润", f"{model.get('developer_margin', 0)*100:.1f}%")
                if "cost_breakdown" in model:
                    st.markdown("**成本构成明细：**")
                    bd = model["cost_breakdown"]
                    fig_pie = go.Figure(go.Pie(
                        labels=list(bd.keys()), values=list(bd.values()),
                        hole=0.4, marker_colors=PLOTLY_COLORS,
                    ))
                    apply_plotly_style(fig_pie, 300)
                    st.plotly_chart(fig_pie, use_container_width=True)
