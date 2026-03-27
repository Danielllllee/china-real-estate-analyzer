"""收益率分析页面 — Premium UI"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.historical_return import calculate_historical_return, compare_purchase_years
from utils.styles import inject_global_css, hero_section, metric_card, apply_plotly_style, get_district_names, PLOTLY_COLORS, COLORS
import yaml

st.set_page_config(page_title="收益率分析", page_icon="📈", layout="wide")
inject_global_css()
hero_section("收益率分析", "计算历史买入的真实回报率，含全成本和IRR分析")

@st.cache_data
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

tab1, tab2 = st.tabs(["单次买入分析", "历史回报对比"])

with tab1:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("#### 买入场景设置")
    col1, col2, col3 = st.columns(3)
    with col1:
        city_names = {k: v["name"] for k, v in config["cities"].items()}
        sc = st.selectbox("城市", list(city_names.values()), key="s_city")
        ck = [k for k, v in config["cities"].items() if v["name"] == sc][0]
        dp = get_district_names(config["cities"][ck])
        sd_idx = st.selectbox("区域", range(len(dp)), format_func=lambda i: dp[i][0], key="s_dist")
        sd = dp[sd_idx][1]
    with col2:
        py = st.number_input("买入年份", 2015, 2025, 2020)
        area = st.number_input("面积（㎡）", 30, 500, 90, key="s_area")
    with col3:
        cp = st.number_input("买入单价（0=历史均价）", 0, 200000, 0)
        dr = st.slider("首付比例", 0.2, 1.0, 0.3, 0.05)

    col4, col5, _ = st.columns(3)
    with col4:
        mr = st.number_input("贷款利率(%)", 1.0, 10.0, 4.5, 0.1) / 100
    with col5:
        my = st.number_input("贷款年限", 5, 30, 30)

    calc = st.button("计算回报", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if calc:
        with st.spinner("计算中..."):
            result = calculate_historical_return(
                sc, sd, purchase_year=py,
                purchase_price_per_sqm=cp if cp > 0 else None,
                area=area, down_payment_ratio=dr,
                mortgage_rate=mr, mortgage_years=my,
            )

        if "error" in result:
            st.error(result["error"])
        else:
            ret = result["returns"]

            # 关键指标
            cols = st.columns(4)
            with cols[0]:
                c = "success" if ret["irr_pct"] > 0 else "danger"
                st.markdown(metric_card("📊", "年化IRR", f"{ret['irr_pct']}%", delta_color=c), unsafe_allow_html=True)
            with cols[1]:
                c = "success" if ret["total_return_pct"] > 0 else "danger"
                st.markdown(metric_card("💰", "总回报率", f"{ret['total_return_pct']}%", delta_color=c), unsafe_allow_html=True)
            with cols[2]:
                st.markdown(metric_card("🏠", f"{py}年买入价", f"{result['purchase_price_per_sqm']:,}元/㎡"), unsafe_allow_html=True)
            with cols[3]:
                st.markdown(metric_card("📈", "当前价格", f"{result['current_price_per_sqm']:,}元/㎡",
                                         f"涨幅 {result['price_change_pct']}%"), unsafe_allow_html=True)

            # 成本与收益
            cost_col, income_col = st.columns(2)
            with cost_col:
                st.markdown("#### 成本明细")
                costs = result["costs"]
                cost_df = pd.DataFrame([
                    {"项目": "首付", "金额(万)": round(costs["down_payment"]/10000, 1)},
                    {"项目": "契税", "金额(万)": round(costs["deed_tax"]/10000, 1)},
                    {"项目": "中介费", "金额(万)": round(costs["agency_fee"]/10000, 1)},
                    {"项目": f"已付月供({result['years_held']}年)", "金额(万)": round(costs["total_mortgage_paid"]/10000, 1)},
                    {"项目": "物业费", "金额(万)": round(costs["property_fee_total"]/10000, 1)},
                    {"项目": "卖出税费", "金额(万)": round(costs["sell_costs"]/10000, 1)},
                ])
                st.dataframe(cost_df, use_container_width=True, hide_index=True)

            with income_col:
                st.markdown("#### 收益瀑布图")
                income = result["income"]
                fig = go.Figure(go.Waterfall(
                    x=["资本增值", "租金收入", "卖出净得", "净利润"],
                    y=[income["capital_gain"], income["rental_income"],
                       income["net_proceeds_from_sale"], ret["net_profit"]],
                    measure=["relative", "relative", "relative", "total"],
                    text=[f"{v/10000:.1f}万" for v in [income["capital_gain"], income["rental_income"],
                          income["net_proceeds_from_sale"], ret["net_profit"]]],
                    increasing_marker_color=COLORS["success"],
                    decreasing_marker_color=COLORS["danger"],
                    totals_marker_color=COLORS["primary"],
                ))
                apply_plotly_style(fig, 350)
                st.plotly_chart(fig, use_container_width=True)

            st.markdown(f"""
            <div class="content-card" style="border-left:4px solid {COLORS['info']};">
                月供：<b>{result['monthly_payment']:,.0f}</b> 元/月 | 剩余贷款：<b>{result['remaining_principal']/10000:.1f}</b> 万元
            </div>
            """, unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("#### 对比设置")
    col1, col2, col3 = st.columns(3)
    with col1:
        cn2 = {k: v["name"] for k, v in config["cities"].items()}
        c2 = st.selectbox("城市", list(cn2.values()), key="c_city")
        ck2 = [k for k, v in config["cities"].items() if v["name"] == c2][0]
        dp2 = get_district_names(config["cities"][ck2])
        d2_idx = st.selectbox("区域", range(len(dp2)), format_func=lambda i: dp2[i][0], key="c_dist")
        d2 = dp2[d2_idx][1]
    with col2:
        a2 = st.number_input("面积（㎡）", 30, 500, 90, key="c_area")
    with col3:
        st.markdown("")  # spacer
    comp_btn = st.button("对比分析", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if comp_btn:
        with st.spinner("计算中..."):
            results = compare_purchase_years(c2, d2, area=a2)
        if not results:
            st.warning("无足够数据")
        else:
            years = [r["purchase_year"] for r in results]
            irrs = [r["returns"]["irr_pct"] for r in results]
            ann = [r["returns"]["annualized_return_pct"] for r in results]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[str(y) for y in years], y=irrs, name="IRR(%)",
                marker_color=[COLORS["success"] if v > 0 else COLORS["danger"] for v in irrs],
            ))
            fig.add_trace(go.Scatter(
                x=[str(y) for y in years], y=ann, name="年化回报(%)",
                mode="lines+markers", line=dict(color=COLORS["accent"], width=3),
                yaxis="y2",
            ))
            fig.update_layout(
                yaxis=dict(title="IRR(%)"), yaxis2=dict(title="年化回报(%)", overlaying="y", side="right"),
                title="不同年份买入的投资回报率",
            )
            apply_plotly_style(fig, 420)
            st.plotly_chart(fig, use_container_width=True)

            compare_df = pd.DataFrame([{
                "买入年份": r["purchase_year"],
                "持有年数": r["years_held"],
                "买入价(元/㎡)": f"{r['purchase_price_per_sqm']:,}",
                "当前价(元/㎡)": f"{r['current_price_per_sqm']:,}",
                "房价涨幅": f"{r['price_change_pct']}%",
                "IRR": f"{r['returns']['irr_pct']}%",
                "年化回报": f"{r['returns']['annualized_return_pct']}%",
                "净利润(万)": f"{r['returns']['net_profit']/10000:.1f}",
            } for r in results])
            st.dataframe(compare_df, use_container_width=True, hide_index=True)
