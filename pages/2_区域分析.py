"""区域深度分析页面 — Premium UI 版本"""
import sys
import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yaml

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from analysis.metrics import get_district_detail, calculate_affordability
from analysis.risk import assess_market_risk
from analysis.advisor import generate_district_report
from models.composite import composite_valuation
from utils.styles import (
    inject_global_css, hero_section, metric_card, score_badge,
    status_tag, content_card, case_card, apply_plotly_style,
    get_district_names, PLOTLY_COLORS, COLORS,
)

st.set_page_config(page_title="区域分析", page_icon="📊", layout="wide")

# ── 全局样式 ──────────────────────────────────────────────────
inject_global_css()


# ── 配置加载 ──────────────────────────────────────────────────
@st.cache_data
def load_config():
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config.yaml",
    )
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()

# ── 城市 / 区域选择 ──────────────────────────────────────────
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

# ── 生成报告 ─────────────────────────────────────────────────
with st.spinner("正在生成智能分析报告..."):
    report = generate_district_report(selected_city, selected_district)

if "error" in report:
    st.warning(report["error"])
    st.stop()

metrics = report["key_metrics"]

# ── Hero 顶部结论卡片 ────────────────────────────────────────
verdict_tag = status_tag(report["verdict"])
badge_html = score_badge(report["score"])

st.markdown(f"""
<div class="hero-section animate-in" style="padding:32px 40px;">
    <div style="display:flex;align-items:center;gap:24px;margin-bottom:20px;position:relative;">
        {badge_html}
        <div>
            <h1 style="margin:0 0 6px;font-size:28px;">{selected_city} · {selected_district}</h1>
            <div style="display:flex;align-items:center;gap:12px;">
                {verdict_tag}
                <span style="font-size:14px;color:#94a3b8;">{report.get('verdict_reason', '')}</span>
            </div>
        </div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:16px;position:relative;">
        <div style="text-align:center;">
            <div style="font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;">均价</div>
            <div style="font-size:22px;font-weight:700;color:white;margin-top:4px;">{metrics['avg_price']:,}<span style="font-size:12px;font-weight:400;color:#94a3b8;"> 元/㎡</span></div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;">租金回报</div>
            <div style="font-size:22px;font-weight:700;color:#10b981;margin-top:4px;">{metrics['annual_yield_pct']}%</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;">近1年涨跌</div>
            <div style="font-size:22px;font-weight:700;color:{'#10b981' if metrics['price_trend_1y_pct'] >= 0 else '#ef4444'};margin-top:4px;">{metrics['price_trend_1y_pct']:+.1f}%</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;">去化周期</div>
            <div style="font-size:22px;font-weight:700;color:white;margin-top:4px;">{metrics['months_of_supply']}<span style="font-size:12px;font-weight:400;color:#94a3b8;"> 月</span></div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;">成交量</div>
            <div style="font-size:22px;font-weight:700;color:white;margin-top:4px;">{metrics['txn_count']}<span style="font-size:12px;font-weight:400;color:#94a3b8;"> 套/月</span></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 主内容 Tabs ──────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📖 投资解读", "🏘️ 板块分析", "📜 历史案例", "⚠️ 风险与估值"])

# ============================================================
# Tab 1 — 投资解读
# ============================================================
with tab1:
    plain_report = report.get("plain_text_report", "")
    if plain_report:
        # Split by markdown headings (## or ###) to create section cards
        import re
        sections = re.split(r'\n(?=#{2,3}\s)', plain_report.strip())
        for section in sections:
            section = section.strip()
            if not section:
                continue
            # Extract heading
            heading_match = re.match(r'^(#{2,3})\s+(.+)', section)
            if heading_match:
                title = heading_match.group(2).strip()
                body = section[heading_match.end():].strip()
            else:
                title = "分析概要"
                body = section
            # Convert remaining markdown to simple HTML
            body_html = body.replace("\n\n", "<br><br>").replace("\n- ", "<br>• ").replace("\n", "<br>")
            content_card(title, f'<div style="font-size:14px;color:#4a5568;line-height:1.8;">{body_html}</div>')

    # Score details table
    if report.get("score_details"):
        st.markdown("")
        score_df = pd.DataFrame(report["score_details"], columns=["指标", "说明", "分数"])
        content_card(
            "评分明细",
            score_df.to_html(index=False, classes="", border=0,
                             escape=False,
                             table_id="score-table"),
        )
        st.markdown("""<style>
        #score-table { width:100%; border-collapse:collapse; font-size:14px; }
        #score-table th { background:#f8f9fc; padding:10px 12px; text-align:left; font-weight:600; color:#334155; border-bottom:2px solid #e2e8f0; }
        #score-table td { padding:10px 12px; border-bottom:1px solid #f0f0f5; color:#4a5568; }
        #score-table tr:hover td { background:#fafbfd; }
        </style>""", unsafe_allow_html=True)

# ============================================================
# Tab 2 — 板块分析
# ============================================================
with tab2:
    sectors = report.get("sector_recommendations", [])
    if sectors:
        sector_df = pd.DataFrame(sectors)

        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            fig_bar = px.bar(
                sector_df.sort_values("avg_price"),
                y="name", x="avg_price", orientation="h",
                color="yield_pct",
                color_continuous_scale="RdYlGn",
                labels={"name": "板块", "avg_price": "均价（元/㎡）", "yield_pct": "租金回报%"},
                title="各板块均价及租金回报率",
            )
            apply_plotly_style(fig_bar, height=max(300, len(sectors) * 45))
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_chart2:
            fig_yield = px.bar(
                sector_df.sort_values("yield_pct", ascending=True),
                y="name", x="yield_pct", orientation="h",
                color="recommendation",
                color_discrete_map={
                    "重点推荐": COLORS["success"],
                    "值得关注": COLORS["warning"],
                    "性价比一般": COLORS["danger"],
                },
                labels={"name": "板块", "yield_pct": "租金回报率（%）"},
                title="各板块租金回报率排名",
            )
            apply_plotly_style(fig_yield, height=max(300, len(sectors) * 45))
            st.plotly_chart(fig_yield, use_container_width=True)

        # Styled sector table
        display_df = sector_df.copy()
        display_df.columns = ["板块", "均价(元/㎡)", "月租金(元/㎡)", "租金回报(%)", "小区数", "投资建议"]
        st.markdown("")
        content_card(
            "板块数据明细",
            display_df.to_html(index=False, classes="", border=0,
                               escape=False,
                               table_id="sector-table"),
        )
        st.markdown("""<style>
        #sector-table { width:100%; border-collapse:collapse; font-size:14px; }
        #sector-table th { background:#f8f9fc; padding:10px 12px; text-align:left; font-weight:600; color:#334155; border-bottom:2px solid #e2e8f0; }
        #sector-table td { padding:10px 12px; border-bottom:1px solid #f0f0f5; color:#4a5568; }
        #sector-table tr:hover td { background:#fafbfd; }
        </style>""", unsafe_allow_html=True)
    else:
        st.info("暂无板块级数据")

# ============================================================
# Tab 3 — 历史案例
# ============================================================
with tab3:
    cases = report.get("case_stories", [])
    if cases:
        profit_cases = [c for c in cases if c["profit"] > 0]
        loss_cases = [c for c in cases if c["profit"] <= 0]

        col_profit, col_loss = st.columns(2)
        with col_profit:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">
                <div style="width:8px;height:8px;border-radius:50%;background:#10b981;"></div>
                <span style="font-size:16px;font-weight:600;color:#1a1a2e;">盈利案例（{len(profit_cases)}个）</span>
            </div>
            """, unsafe_allow_html=True)
            for c in profit_cases[:6]:
                st.markdown(
                    case_card(c["sector"], c["community"], c["year"],
                              c["profit"], c["return_pct"], c["story"]),
                    unsafe_allow_html=True,
                )

        with col_loss:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">
                <div style="width:8px;height:8px;border-radius:50%;background:#ef4444;"></div>
                <span style="font-size:16px;font-weight:600;color:#1a1a2e;">亏损案例（{len(loss_cases)}个）</span>
            </div>
            """, unsafe_allow_html=True)
            for c in loss_cases[:6]:
                st.markdown(
                    case_card(c["sector"], c["community"], c["year"],
                              c["profit"], c["return_pct"], c["story"]),
                    unsafe_allow_html=True,
                )

        # Scatter chart
        case_df = pd.DataFrame(cases)
        if not case_df.empty:
            fig_scatter = px.scatter(
                case_df, x="year", y="return_pct",
                size=[abs(p) + 1 for p in case_df["profit"]],
                color=["盈利" if p > 0 else "亏损" for p in case_df["profit"]],
                color_discrete_map={"盈利": COLORS["success"], "亏损": COLORS["danger"]},
                hover_data=["sector", "community", "profit"],
                labels={"year": "买入年份", "return_pct": "年化回报率(%)", "color": "盈亏"},
                title="不同年份买入的年化回报率分布",
            )
            apply_plotly_style(fig_scatter, height=420)
            st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("暂无历史案例数据")

# ============================================================
# Tab 4 — 风险与估值
# ============================================================
with tab4:
    # ── 风险评估 ──
    risk = report.get("risk")
    if risk:
        st.markdown("")
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.markdown(metric_card("🎯", "风险评分", f"{risk['risk_score']}/100"), unsafe_allow_html=True)
        with r2:
            st.markdown(metric_card("📊", "风险等级", risk["risk_level"]), unsafe_allow_html=True)
        with r3:
            st.markdown(metric_card("📈", "价格波动率", f"{risk['volatility']*100:.1f}%"), unsafe_allow_html=True)
        with r4:
            st.markdown(metric_card("🏠", "库存去化月数", f"{risk['months_of_inventory']:.1f}"), unsafe_allow_html=True)

        if risk.get("risk_factors"):
            factors_html = "".join(
                f'<div style="padding:10px 16px;background:#fef2f2;border-radius:8px;margin-bottom:8px;'
                f'border-left:3px solid #ef4444;font-size:14px;color:#991b1b;">'
                f'⚠️ {rf}</div>'
                for rf in risk["risk_factors"]
            )
            content_card("风险因素", factors_html)

    # ── 购房负担分析 ──
    afford = report.get("affordability")
    if afford:
        st.markdown("")
        st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
        a1, a2, a3 = st.columns(3)
        with a1:
            st.markdown(metric_card("💰", "90㎡总价", f"{afford['total_price']/10000:.0f}万元"), unsafe_allow_html=True)
        with a2:
            st.markdown(metric_card("📐", "房价收入比", f"{afford['price_to_income_ratio']}"), unsafe_allow_html=True)
        with a3:
            st.markdown(metric_card("💳", "月供收入比", f"{afford['payment_to_income_ratio']:.0%}"), unsafe_allow_html=True)

        content_card("负担评估", f'<div style="font-size:14px;color:#4a5568;line-height:1.8;">{afford["assessment"]}</div>')

    # ── 综合估值 ──
    detail = get_district_detail(selected_city, selected_district)
    if not detail["communities"].empty:
        valuation = composite_valuation(
            selected_city, selected_district,
            current_price_per_sqm=detail["communities"]["avg_listing_price"].median(),
        )
        if "error" not in valuation:
            comp = valuation["composite"]
            st.markdown("")
            st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
            v1, v2, v3 = st.columns(3)
            with v1:
                st.markdown(metric_card("🔻", "保守估值", f"{comp['conservative_value']:,} 元/㎡"), unsafe_allow_html=True)
            with v2:
                st.markdown(metric_card("⚖️", "中性估值", f"{comp['fair_value_per_sqm']:,} 元/㎡"), unsafe_allow_html=True)
            with v3:
                st.markdown(metric_card("🔺", "乐观估值", f"{comp['optimistic_value']:,} 元/㎡"), unsafe_allow_html=True)

            if "composite_assessment" in valuation:
                ca = valuation["composite_assessment"]
                content_card(
                    "估值结论",
                    f'<div style="font-size:15px;color:#1a1a2e;font-weight:600;">{ca["recommendation"]}</div>'
                    f'<div style="font-size:14px;color:#64748b;margin-top:6px;">当前挂牌价偏离综合估值 {ca["deviation_pct"]}</div>',
                )

    # ── 价格趋势 ──
    pt = detail.get("price_trend", pd.DataFrame())
    if isinstance(pt, pd.DataFrame) and not pt.empty:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=pt["month"], y=pt["avg_unit_price"],
            mode="lines", name="均价",
            line=dict(color=COLORS["primary"], width=2.5),
            fill="tozeroy",
            fillcolor="rgba(15,52,96,0.06)",
        ))
        fig_trend.add_trace(go.Scatter(
            x=pt["month"], y=pt["median_unit_price"],
            mode="lines", name="中位价",
            line=dict(color=COLORS["accent"], width=2, dash="dash"),
        ))
        fig_trend.update_layout(
            title="价格趋势",
            yaxis_title="元/㎡",
            hovermode="x unified",
        )
        apply_plotly_style(fig_trend, height=380)
        st.plotly_chart(fig_trend, use_container_width=True)

# ── 区域内小区列表 ────────────────────────────────────────────
st.markdown("")
detail = get_district_detail(selected_city, selected_district)
if not detail["communities"].empty:
    comm = detail["communities"][["name", "build_year", "avg_listing_price", "listing_count", "property_fee"]].copy()
    comm.columns = ["小区名称", "建成年份", "挂牌均价(元/㎡)", "在售套数", "物业费(元/㎡/月)"]
    comm = comm.sort_values("挂牌均价(元/㎡)", ascending=False)
    content_card(
        f"区域内小区（{len(comm)}个）",
        comm.to_html(index=False, classes="", border=0, escape=False, table_id="comm-table"),
    )
    st.markdown("""<style>
    #comm-table { width:100%; border-collapse:collapse; font-size:14px; }
    #comm-table th { background:#f8f9fc; padding:10px 12px; text-align:left; font-weight:600; color:#334155; border-bottom:2px solid #e2e8f0; }
    #comm-table td { padding:10px 12px; border-bottom:1px solid #f0f0f5; color:#4a5568; }
    #comm-table tr:hover td { background:#fafbfd; }
    </style>""", unsafe_allow_html=True)
