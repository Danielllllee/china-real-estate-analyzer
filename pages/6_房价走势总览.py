"""全城市房价走势总览 — 标注历史最高点与当前价格"""
import sys
import os
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import yaml

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.database import query_df
from core.styles import (
    inject_global_css,
    hero_section,
    apply_plotly_style,
    PLOTLY_COLORS,
    COLORS,
)

st.set_page_config(page_title="房价走势总览", page_icon="📈", layout="wide")
inject_global_css()
hero_section("全城市房价走势总览", "所有城市长期房价变化趋势，标注历史最高点与当前价格")


# ============ 加载配置 ============
@st.cache_data
def load_config():
    with open(os.path.join(_ROOT, "config.yaml"), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()
city_names = [v["name"] for v in config["cities"].values()]


# ============ 数据查询 ============
@st.cache_data(ttl=600)
def get_city_monthly_trend(city: str) -> pd.DataFrame:
    """获取城市月度均价走势（district_stats 2020-2026）"""
    return query_df("""
        SELECT month,
               ROUND(AVG(avg_unit_price)) as avg_price,
               ROUND(AVG(median_unit_price)) as median_price
        FROM district_stats
        WHERE city = ?
        GROUP BY month
        ORDER BY month
    """, [city])


@st.cache_data(ttl=600)
def get_city_yearly_trend(city: str) -> pd.DataFrame:
    """从 district_stats 聚合年度均价（2015-2026）"""
    return query_df("""
        SELECT SUBSTR(month, 1, 4) as year,
               ROUND(AVG(avg_unit_price)) as avg_price,
               SUM(transaction_count) as deal_count
        FROM district_stats
        WHERE city = ?
        GROUP BY SUBSTR(month, 1, 4)
        ORDER BY year
    """, [city])


@st.cache_data(ttl=600)
def get_district_monthly_trend(city: str) -> pd.DataFrame:
    """获取城市各区域的月度均价走势"""
    return query_df("""
        SELECT district, month, avg_unit_price
        FROM district_stats
        WHERE city = ?
        ORDER BY district, month
    """, [city])


# ============ 绘图辅助 ============
def make_city_trend_chart(city: str, monthly: pd.DataFrame, yearly: pd.DataFrame):
    """生成单个城市的走势图，标注最高点和当前价格"""
    fig = go.Figure()

    # --- 年度长周期趋势线 ---
    if not yearly.empty and len(yearly) > 1:
        fig.add_trace(go.Scatter(
            x=yearly["year"],
            y=yearly["avg_price"],
            mode="lines+markers",
            name="年度均价（成交）",
            line=dict(color=PLOTLY_COLORS[1], width=2, dash="dot"),
            marker=dict(size=8, color=PLOTLY_COLORS[1]),
            hovertemplate="<b>%{x}年</b><br>成交均价: %{y:,.0f} 元/㎡<extra></extra>",
        ))

        # 标注年度最高点
        peak_idx = yearly["avg_price"].idxmax()
        peak_row = yearly.loc[peak_idx]
        fig.add_trace(go.Scatter(
            x=[peak_row["year"]],
            y=[peak_row["avg_price"]],
            mode="markers+text",
            name="年度最高",
            marker=dict(size=14, color=PLOTLY_COLORS[1], symbol="star"),
            text=[f"峰值 {peak_row['avg_price']:,.0f}"],
            textposition="top center",
            textfont=dict(size=11, color=PLOTLY_COLORS[1], family="sans-serif"),
            showlegend=False,
            hoverinfo="skip",
        ))

    # --- 月度趋势线 ---
    if not monthly.empty and len(monthly) > 1:
        fig.add_trace(go.Scatter(
            x=monthly["month"],
            y=monthly["avg_price"],
            mode="lines",
            name="月度均价（统计）",
            line=dict(color=PLOTLY_COLORS[0], width=3),
            fill="tozeroy",
            fillcolor="rgba(15,52,96,0.06)",
            hovertemplate="<b>%{x}</b><br>均价: %{y:,.0f} 元/㎡<extra></extra>",
        ))

        # 月度最高点
        peak_idx = monthly["avg_price"].idxmax()
        peak_row = monthly.loc[peak_idx]
        fig.add_trace(go.Scatter(
            x=[peak_row["month"]],
            y=[peak_row["avg_price"]],
            mode="markers+text",
            name="月度最高",
            marker=dict(size=16, color=COLORS["accent"], symbol="triangle-up",
                        line=dict(width=2, color="white")),
            text=[f"最高 {peak_row['avg_price']:,.0f}"],
            textposition="top center",
            textfont=dict(size=12, color=COLORS["accent"], family="sans-serif"),
            showlegend=False,
            hoverinfo="skip",
        ))

        # 当前价格（最后一个月）
        current = monthly.iloc[-1]
        fig.add_trace(go.Scatter(
            x=[current["month"]],
            y=[current["avg_price"]],
            mode="markers+text",
            name="当前价格",
            marker=dict(size=14, color=COLORS["success"], symbol="circle",
                        line=dict(width=2, color="white")),
            text=[f"当前 {current['avg_price']:,.0f}"],
            textposition="bottom center",
            textfont=dict(size=12, color=COLORS["success"], family="sans-serif"),
            showlegend=False,
            hoverinfo="skip",
        ))

        # 计算跌幅
        change_pct = (current["avg_price"] - peak_row["avg_price"]) / peak_row["avg_price"] * 100
        change_text = f"较最高点 {change_pct:+.1f}%" if change_pct != 0 else "持平"
        change_color = COLORS["success"] if change_pct >= 0 else COLORS["accent"]

        fig.add_annotation(
            x=0.5, y=1.08, xref="paper", yref="paper",
            text=f"<b>{city}</b>　当前 <b>{current['avg_price']:,.0f}</b> 元/㎡　|　"
                 f"峰值 <b>{peak_row['avg_price']:,.0f}</b> 元/㎡　|　"
                 f"<span style='color:{change_color}'>{change_text}</span>",
            showarrow=False,
            font=dict(size=13),
            align="center",
        )

    apply_plotly_style(fig, height=400)
    fig.update_layout(
        xaxis=dict(title=""),
        yaxis=dict(title="均价（元/㎡）"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=60, b=60),
    )
    return fig


def make_district_trend_chart(city: str, df: pd.DataFrame):
    """生成城市各区域走势对比图"""
    fig = go.Figure()
    districts = df["district"].unique()
    colors = PLOTLY_COLORS * 3  # 确保颜色够用

    for i, district in enumerate(districts):
        ddf = df[df["district"] == district]
        fig.add_trace(go.Scatter(
            x=ddf["month"],
            y=ddf["avg_unit_price"],
            mode="lines",
            name=district,
            line=dict(color=colors[i % len(colors)], width=2),
            hovertemplate=f"<b>{district}</b><br>" + "%{x}<br>均价: %{y:,.0f} 元/㎡<extra></extra>",
        ))

        # 标注每个区域的最高点
        if not ddf.empty:
            peak_idx = ddf["avg_unit_price"].idxmax()
            peak = ddf.loc[peak_idx]
            fig.add_trace(go.Scatter(
                x=[peak["month"]],
                y=[peak["avg_unit_price"]],
                mode="markers",
                marker=dict(size=8, color=colors[i % len(colors)], symbol="triangle-up",
                            line=dict(width=1, color="white")),
                showlegend=False,
                hovertemplate=f"<b>{district} 最高点</b><br>{peak['month']}<br>"
                              f"{peak['avg_unit_price']:,.0f} 元/㎡<extra></extra>",
            ))

    apply_plotly_style(fig, height=500)
    fig.update_layout(
        title=dict(text=f"{city} — 各区域月度均价走势", font=dict(size=16)),
        xaxis=dict(title=""),
        yaxis=dict(title="均价（元/㎡）"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=50, b=70),
    )
    return fig


# ============ 页面布局 ============
view_mode = st.radio(
    "查看模式",
    ["所有城市总览", "单城市详细"],
    horizontal=True,
    label_visibility="collapsed",
)

if view_mode == "所有城市总览":
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{COLORS['primary']},#1a5276);
                color:white;border-radius:12px;padding:16px 24px;margin-bottom:24px;">
        <p style="margin:0;font-size:14px;">
        📊 展示所有 <b>{len(city_names)}</b> 个城市的房价走势，数据来源：月度区域统计（2020-2026）+ 历史成交记录（2015-2026）。
        红色三角标注月度最高点，绿色圆点标注当前价格。
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 两列布局展示所有城市
    cols = st.columns(2)
    for idx, city in enumerate(city_names):
        with cols[idx % 2]:
            monthly = get_city_monthly_trend(city)
            yearly = get_city_yearly_trend(city)
            if monthly.empty and yearly.empty:
                st.info(f"{city}：暂无数据")
                continue
            fig = make_city_trend_chart(city, monthly, yearly)
            st.plotly_chart(fig, use_container_width=True, key=f"city_{idx}")

    # ============ 汇总对比表格 ============
    st.markdown("---")
    st.markdown(f'<h2 style="color:{COLORS["primary"]};">各城市房价变化汇总</h2>',
                unsafe_allow_html=True)

    summary_rows = []
    for city in city_names:
        monthly = get_city_monthly_trend(city)
        yearly = get_city_yearly_trend(city)
        if monthly.empty:
            continue
        peak_price = monthly["avg_price"].max()
        peak_month = monthly.loc[monthly["avg_price"].idxmax(), "month"]
        current_price = monthly.iloc[-1]["avg_price"]
        current_month = monthly.iloc[-1]["month"]
        change_pct = (current_price - peak_price) / peak_price * 100

        earliest_yearly = yearly.iloc[0]["avg_price"] if not yearly.empty else None
        earliest_year = yearly.iloc[0]["year"] if not yearly.empty else None
        long_change = ((current_price - earliest_yearly) / earliest_yearly * 100) if earliest_yearly else None

        summary_rows.append({
            "城市": city,
            "当前均价(元/㎡)": current_price,
            "当前月份": current_month,
            "历史最高(元/㎡)": peak_price,
            "最高月份": peak_month,
            "较最高点跌幅": change_pct,
            f"较{earliest_year}年变化" if earliest_year else "长期变化": long_change,
        })

    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        # 统一列名
        display_cols = ["城市", "当前均价(元/㎡)", "历史最高(元/㎡)", "最高月份", "较最高点跌幅"]
        # 找到长期变化列
        long_col = [c for c in summary_df.columns if "变化" in c]
        if long_col:
            display_cols.append(long_col[0])

        st.dataframe(
            summary_df[display_cols].style.format({
                "当前均价(元/㎡)": "{:,.0f}",
                "历史最高(元/㎡)": "{:,.0f}",
                "较最高点跌幅": "{:+.1f}%",
            }).applymap(
                lambda v: f"color: {COLORS['accent']}" if isinstance(v, (int, float)) and v < 0
                else f"color: {COLORS['success']}" if isinstance(v, (int, float)) and v > 0
                else "",
                subset=["较最高点跌幅"],
            ),
            use_container_width=True,
            hide_index=True,
            height=min(600, 40 + len(summary_rows) * 35),
        )

else:
    # ============ 单城市详细模式 ============
    selected_city = st.selectbox("选择城市", city_names, label_visibility="collapsed")

    monthly = get_city_monthly_trend(selected_city)
    yearly = get_city_yearly_trend(selected_city)
    district_data = get_district_monthly_trend(selected_city)

    if monthly.empty:
        st.warning("暂无该城市数据")
        st.stop()

    # 城市总体走势
    st.markdown(f'<h2 style="color:{COLORS["primary"]};">{selected_city} 房价走势</h2>',
                unsafe_allow_html=True)
    fig_main = make_city_trend_chart(selected_city, monthly, yearly)
    fig_main.update_layout(height=480)
    st.plotly_chart(fig_main, use_container_width=True)

    # 各区域走势对比
    st.markdown("---")
    if not district_data.empty:
        fig_districts = make_district_trend_chart(selected_city, district_data)
        st.plotly_chart(fig_districts, use_container_width=True)

    # 各区域汇总表
    st.markdown("---")
    st.markdown(f'<h3 style="color:{COLORS["primary"]};">各区域房价变化明细</h3>',
                unsafe_allow_html=True)

    district_summary = []
    for district in district_data["district"].unique():
        ddf = district_data[district_data["district"] == district]
        if ddf.empty:
            continue
        peak_price = ddf["avg_unit_price"].max()
        peak_month = ddf.loc[ddf["avg_unit_price"].idxmax(), "month"]
        current_price = ddf.iloc[-1]["avg_unit_price"]
        change = (current_price - peak_price) / peak_price * 100
        district_summary.append({
            "区域": district,
            "当前均价(元/㎡)": current_price,
            "历史最高(元/㎡)": peak_price,
            "最高月份": peak_month,
            "较最高点": change,
        })

    if district_summary:
        ds_df = pd.DataFrame(district_summary).sort_values("当前均价(元/㎡)", ascending=False)
        st.dataframe(
            ds_df.style.format({
                "当前均价(元/㎡)": "{:,.0f}",
                "历史最高(元/㎡)": "{:,.0f}",
                "较最高点": "{:+.1f}%",
            }).applymap(
                lambda v: f"color: {COLORS['accent']}" if isinstance(v, (int, float)) and v < 0
                else f"color: {COLORS['success']}" if isinstance(v, (int, float)) and v > 0
                else "",
                subset=["较最高点"],
            ),
            use_container_width=True,
            hide_index=True,
        )
