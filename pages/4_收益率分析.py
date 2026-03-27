"""收益率分析页面"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.historical_return import calculate_historical_return, compare_purchase_years
import yaml

st.set_page_config(page_title="收益率分析", page_icon="📈", layout="wide")
st.title("收益率分析")

@st.cache_data
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

tab1, tab2 = st.tabs(["单次买入分析", "历史回报对比"])

with tab1:
    st.subheader("计算特定买入场景的投资回报")

    col1, col2 = st.columns(2)
    with col1:
        city_names = {k: v["name"] for k, v in config["cities"].items()}
        selected_city = st.selectbox("城市", list(city_names.values()), key="single_city")
        city_key = [k for k, v in config["cities"].items() if v["name"] == selected_city][0]
        district_names = [d["name"] for d in config["cities"][city_key]["districts"]]
        selected_district = st.selectbox("区域", district_names, key="single_district")
        purchase_year = st.number_input("买入年份", 2015, 2024, 2020)
        area = st.number_input("面积（㎡）", 30, 500, 90, key="single_area")

    with col2:
        custom_price = st.number_input("买入单价（元/㎡，0=使用历史均价）", 0, 200000, 0)
        down_ratio = st.slider("首付比例", 0.2, 1.0, 0.3, 0.05)
        mortgage_rate = st.number_input("贷款利率（%）", 1.0, 10.0, 4.5, 0.1) / 100
        mortgage_years = st.number_input("贷款年限", 5, 30, 30)

    if st.button("计算回报", type="primary"):
        with st.spinner("计算中..."):
            result = calculate_historical_return(
                selected_city, selected_district,
                purchase_year=purchase_year,
                purchase_price_per_sqm=custom_price if custom_price > 0 else None,
                area=area,
                down_payment_ratio=down_ratio,
                mortgage_rate=mortgage_rate,
                mortgage_years=mortgage_years,
            )

        if "error" in result:
            st.error(result["error"])
        else:
            st.markdown("---")
            st.subheader("投资回报分析")

            # 关键指标
            ret = result["returns"]
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("年化IRR", f"{ret['irr_pct']}%")
            with col2:
                st.metric("总回报率", f"{ret['total_return_pct']}%")
            with col3:
                st.metric("年化回报", f"{ret['annualized_return_pct']}%")
            with col4:
                st.metric("房价涨幅", f"{result['price_change_pct']}%")

            # 价格对比
            col1, col2 = st.columns(2)
            with col1:
                st.metric(f"{purchase_year}年买入价", f"{result['purchase_price_per_sqm']:,} 元/㎡")
            with col2:
                st.metric("当前价格", f"{result['current_price_per_sqm']:,} 元/㎡")

            # 成本构成
            st.subheader("成本明细")
            costs = result["costs"]
            cost_items = {
                "首付": costs["down_payment"],
                "契税": costs["deed_tax"],
                "中介费": costs["agency_fee"],
                f"已付月供（{result['years_held']}年）": costs["total_mortgage_paid"],
                f"物业费（{result['years_held']}年）": costs["property_fee_total"],
                "卖出税费": costs["sell_costs"],
            }
            cost_df = pd.DataFrame([
                {"项目": k, "金额（元）": v, "金额（万元）": round(v/10000, 1)}
                for k, v in cost_items.items()
            ])
            st.dataframe(cost_df, use_container_width=True, hide_index=True)

            # 收益构成
            st.subheader("收益构成")
            income = result["income"]
            fig_income = go.Figure(go.Waterfall(
                x=["资本增值", "租金收入", "卖出净得", "净利润"],
                y=[income["capital_gain"], income["rental_income"],
                   income["net_proceeds_from_sale"], ret["net_profit"]],
                measure=["relative", "relative", "relative", "total"],
                text=[f"{v/10000:.1f}万" for v in [income["capital_gain"], income["rental_income"],
                      income["net_proceeds_from_sale"], ret["net_profit"]]],
                connector={"line": {"color": "rgb(63, 63, 63)"}},
            ))
            fig_income.update_layout(title="收益瀑布图", height=400)
            st.plotly_chart(fig_income, use_container_width=True)

            # 月供信息
            st.info(f"月供：{result['monthly_payment']:,.0f} 元/月 | "
                    f"剩余贷款：{result['remaining_principal']/10000:.1f} 万元")


with tab2:
    st.subheader("不同年份买入的回报率对比")

    col1, col2 = st.columns(2)
    with col1:
        city_names2 = {k: v["name"] for k, v in config["cities"].items()}
        city2 = st.selectbox("城市", list(city_names2.values()), key="compare_city")
        city_key2 = [k for k, v in config["cities"].items() if v["name"] == city2][0]
        districts2 = [d["name"] for d in config["cities"][city_key2]["districts"]]
        district2 = st.selectbox("区域", districts2, key="compare_district")
    with col2:
        area2 = st.number_input("面积（㎡）", 30, 500, 90, key="compare_area")

    if st.button("对比分析", type="primary"):
        with st.spinner("计算中..."):
            results = compare_purchase_years(city2, district2, area=area2)

        if not results:
            st.warning("无足够数据进行对比")
        else:
            st.markdown("---")

            # IRR对比图
            years = [r["purchase_year"] for r in results]
            irrs = [r["returns"]["irr_pct"] for r in results]
            annualized = [r["returns"]["annualized_return_pct"] for r in results]
            price_changes = [r["price_change_pct"] for r in results]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[str(y) for y in years], y=irrs,
                name="IRR",
                marker_color=["#66bb6a" if v > 0 else "#ef5350" for v in irrs],
            ))
            fig.add_trace(go.Scatter(
                x=[str(y) for y in years], y=annualized,
                name="年化回报",
                mode="lines+markers",
                line=dict(color="#ff9800", width=2),
                yaxis="y2",
            ))
            fig.update_layout(
                title="不同年份买入的投资回报率",
                yaxis=dict(title="IRR（%）"),
                yaxis2=dict(title="年化回报（%）", overlaying="y", side="right"),
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

            # 详细对比表
            compare_df = pd.DataFrame([{
                "买入年份": r["purchase_year"],
                "持有年数": r["years_held"],
                "买入价(元/㎡)": f"{r['purchase_price_per_sqm']:,}",
                "当前价(元/㎡)": f"{r['current_price_per_sqm']:,}",
                "房价涨幅": f"{r['price_change_pct']}%",
                "IRR": f"{r['returns']['irr_pct']}%",
                "年化回报": f"{r['returns']['annualized_return_pct']}%",
                "总回报": f"{r['returns']['total_return_pct']}%",
                "净利润(万)": f"{r['returns']['net_profit']/10000:.1f}",
            } for r in results])
            st.dataframe(compare_df, use_container_width=True, hide_index=True)
