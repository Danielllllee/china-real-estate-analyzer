"""单套房产估值计算器"""
import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.composite import composite_valuation
from utils.database import query_df
import yaml

st.set_page_config(page_title="估值计算器", page_icon="🧮", layout="wide")
st.title("单套房产估值计算器")

@st.cache_data
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

st.markdown("输入房产基本信息，系统将使用四个模型进行综合估值。")

# 输入区域
col1, col2 = st.columns(2)
with col1:
    city_names = {k: v["name"] for k, v in config["cities"].items()}
    selected_city = st.selectbox("城市", list(city_names.values()))
    city_key = [k for k, v in config["cities"].items() if v["name"] == selected_city][0]
    district_names = [d["name"] for d in config["cities"][city_key]["districts"]]
    selected_district = st.selectbox("区域", district_names)
    area = st.number_input("面积（㎡）", min_value=20, max_value=500, value=90)
    building_age = st.number_input("房龄（年）", min_value=0, max_value=50, value=10)

with col2:
    floor_level = st.selectbox("楼层", ["low", "mid", "mid_high", "high"],
                                format_func=lambda x: {"low": "低楼层(1-6)", "mid": "中楼层(7-15)",
                                                        "mid_high": "中高楼层(16-25)", "high": "高楼层(26+)"}[x])
    decoration = st.selectbox("装修", ["rough", "simple", "fine", "luxury"],
                               format_func=lambda x: {"rough": "毛坯", "simple": "简装",
                                                       "fine": "精装", "luxury": "豪装"}[x])
    orientation = st.selectbox("朝向", ["south", "south_north", "east", "west", "north"],
                                format_func=lambda x: {"south": "南", "south_north": "南北通透",
                                                        "east": "东", "west": "西", "north": "北"}[x])
    current_price = st.number_input("当前挂牌价（元/㎡，选填）", min_value=0, value=0,
                                     help="输入实际挂牌价以对比估值偏离度，0表示不对比")

if st.button("开始估值", type="primary"):
    with st.spinner("正在计算..."):
        result = composite_valuation(
            city=selected_city,
            district=selected_district,
            area=area,
            floor_level=floor_level,
            decoration=decoration,
            building_age=building_age,
            orientation=orientation,
            current_price_per_sqm=current_price if current_price > 0 else None,
        )

    if "error" in result:
        st.error(result["error"])
        st.stop()

    comp = result["composite"]

    # 综合估值结果
    st.markdown("---")
    st.subheader("综合估值结果")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("保守估值", f"{comp['conservative_value']:,} 元/㎡",
                   f"总价 {comp['conservative_total_price']} 万")
    with col2:
        st.metric("中性估值", f"{comp['fair_value_per_sqm']:,} 元/㎡",
                   f"总价 {comp['fair_total_price']} 万")
    with col3:
        st.metric("乐观估值", f"{comp['optimistic_value']:,} 元/㎡",
                   f"总价 {comp['optimistic_total_price']} 万")

    # 与挂牌价对比
    if "composite_assessment" in result:
        st.markdown("---")
        st.subheader("价格评估")
        ca = result["composite_assessment"]
        col1, col2 = st.columns(2)
        with col1:
            st.metric("当前挂牌价", f"{ca['current_price']:,} 元/㎡")
            st.metric("综合估值", f"{ca['composite_fair_value']:,} 元/㎡")
        with col2:
            color = "🟢" if float(ca["deviation_pct"].strip("%+")) < 0 else "🔴"
            st.metric("偏离度", ca["deviation_pct"])
            st.info(f"{color} **{ca['recommendation']}**")

    # 各模型详细结果
    st.markdown("---")
    st.subheader("各模型估值详情")

    models = result["models"]

    # 可视化对比
    model_names = []
    fair_vals = []
    cons_vals = []
    opt_vals = []

    for key, model in models.items():
        if "fair_value_per_sqm" in model:
            model_names.append(model["model_name"])
            fair_vals.append(model["fair_value_per_sqm"])
            cons_vals.append(model["conservative_value"])
            opt_vals.append(model["optimistic_value"])

    if model_names:
        fig = go.Figure()
        fig.add_trace(go.Bar(name="保守", x=model_names, y=cons_vals, marker_color="#ef5350"))
        fig.add_trace(go.Bar(name="中性", x=model_names, y=fair_vals, marker_color="#42a5f5"))
        fig.add_trace(go.Bar(name="乐观", x=model_names, y=opt_vals, marker_color="#66bb6a"))

        if current_price > 0:
            fig.add_hline(y=current_price, line_dash="dash", line_color="orange",
                          annotation_text=f"当前挂牌价 {current_price:,}")

        fig.update_layout(barmode="group", yaxis_title="元/㎡", height=400)
        st.plotly_chart(fig, use_container_width=True)

    # 各模型详细参数
    for key, model in models.items():
        with st.expander(f"{model['model_name']} 详细参数"):
            if key == "rental_yield":
                st.write(f"- 年毛租金：{model.get('gross_annual_rent_per_sqm', 'N/A')} 元/㎡")
                st.write(f"- 年净租金：{model.get('net_annual_rent_per_sqm', 'N/A')} 元/㎡")
                st.write(f"- 资本化率：{model.get('cap_rate', 0)*100:.2f}%")
                st.write(f"- 无风险利率：{model.get('risk_free_rate', 0)*100:.2f}%")
                st.write(f"- 风险溢价：{model.get('risk_premium', 0)*100:.2f}%")
            elif key == "comparable":
                st.write(f"- 可比样本数：{model.get('sample_count', 'N/A')}")
                st.write(f"- 对比层级：{'同小区' if model.get('comparison_level') == 'community' else '同区域'}")
                st.write(f"- 价格区间：{model.get('price_range', 'N/A')}")
                st.write(f"- 标准差：{model.get('std_dev', 'N/A')}")
            elif key == "dcf":
                st.write(f"- 折现率：{model.get('discount_rate', 0)*100:.2f}%")
                st.write(f"- 租金增长率：{model.get('rent_growth_rate', 0)*100:.2f}%")
                st.write(f"- 预测期：{model.get('projection_years', 'N/A')} 年")
                st.write(f"- 终值占比：{model.get('terminal_share', 'N/A')}%")
                st.write(f"- 租金现值：{model.get('pv_rental_income', 'N/A')} 元/㎡")
                st.write(f"- 终值现值：{model.get('pv_terminal_value', 'N/A')} 元/㎡")
            elif key == "cost_approach":
                st.write(f"- 土地楼面价：{model.get('land_cost', 'N/A')} 元/㎡")
                st.write(f"- 建造成本：{model.get('construction_cost', 'N/A')} 元/㎡")
                st.write(f"- 开发商利润率：{model.get('developer_margin', 0)*100:.1f}%")
                if "cost_breakdown" in model:
                    st.write("**成本构成：**")
                    for item, val in model["cost_breakdown"].items():
                        st.write(f"  - {item}：{val:,} 元/㎡")

    # 错误信息
    if result.get("errors"):
        st.markdown("---")
        st.caption("部分模型数据缺失：" + "；".join(result["errors"]))
