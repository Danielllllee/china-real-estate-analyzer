"""全局样式系统 — 统一的CSS和UI组件"""
import streamlit as st

# 配色方案
COLORS = {
    "primary": "#0f3460",
    "primary_light": "#1a5276",
    "accent": "#e94560",
    "accent_light": "#ff6b81",
    "bg_dark": "#1a1a2e",
    "bg_card": "#ffffff",
    "bg_page": "#f8f9fc",
    "text": "#2c3e50",
    "text_light": "#7f8c8d",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "info": "#3b82f6",
    "border": "#e2e8f0",
    "gold": "#d4a953",
}

# Plotly统一模板
PLOTLY_COLORS = ["#0f3460", "#e94560", "#10b981", "#f59e0b", "#3b82f6", "#8b5cf6", "#06b6d4"]

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="sans-serif", color="#2c3e50"),
    margin=dict(l=20, r=20, t=40, b=20),
    hoverlabel=dict(bgcolor="white", font_size=13),
)


def inject_global_css():
    """注入全局CSS样式"""
    st.markdown("""
    <style>
    /* ============ 全局基础 ============ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        background: linear-gradient(135deg, #f8f9fc 0%, #eef2f7 100%);
    }
    .stApp > header { background: transparent; }

    /* 隐藏默认元素 */
    #MainMenu, footer, .stDeployButton { display: none !important; }

    /* ============ 侧边栏美化 ============ */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #0f3460 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] span {
        color: #cbd5e1 !important;
    }
    section[data-testid="stSidebar"] a {
        color: #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] a:hover {
        color: #ffffff !important;
    }

    /* ============ 卡片组件 ============ */
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.04);
        border: 1px solid #f0f0f5;
        transition: all 0.3s ease;
        height: 100%;
    }
    .metric-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1), 0 8px 24px rgba(0,0,0,0.06);
        transform: translateY(-2px);
    }
    .metric-card .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #1a1a2e;
        margin: 8px 0 4px;
    }
    .metric-card .metric-label {
        font-size: 13px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 500;
    }
    .metric-card .metric-delta {
        font-size: 13px;
        font-weight: 600;
        margin-top: 4px;
    }
    .metric-card .metric-icon {
        font-size: 32px;
        margin-bottom: 4px;
    }

    /* ============ Hero 区域 ============ */
    .hero-section {
        background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 60%, #16213e 100%);
        border-radius: 20px;
        padding: 40px 48px;
        margin-bottom: 32px;
        color: white;
        position: relative;
        overflow: hidden;
    }
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(233,69,96,0.15) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-section h1 {
        font-size: 32px;
        font-weight: 700;
        margin: 0 0 8px;
        position: relative;
    }
    .hero-section p {
        font-size: 16px;
        color: #cbd5e1;
        margin: 0;
        position: relative;
    }

    /* ============ 评分徽章 ============ */
    .score-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 72px;
        height: 72px;
        border-radius: 50%;
        font-size: 24px;
        font-weight: 700;
        color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .score-badge.green { background: linear-gradient(135deg, #10b981, #059669); }
    .score-badge.yellow { background: linear-gradient(135deg, #f59e0b, #d97706); }
    .score-badge.orange { background: linear-gradient(135deg, #f97316, #ea580c); }
    .score-badge.red { background: linear-gradient(135deg, #ef4444, #dc2626); }

    /* ============ 状态标签 ============ */
    .status-tag {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    .status-tag.buy { background: #d1fae5; color: #065f46; }
    .status-tag.hold { background: #fef3c7; color: #92400e; }
    .status-tag.caution { background: #fed7aa; color: #9a3412; }
    .status-tag.avoid { background: #fecaca; color: #991b1b; }

    /* ============ 内容卡片 ============ */
    .content-card {
        background: white;
        border-radius: 16px;
        padding: 28px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.04);
        border: 1px solid #f0f0f5;
        margin-bottom: 20px;
    }
    .content-card h3 {
        color: #1a1a2e;
        font-size: 18px;
        font-weight: 600;
        margin: 0 0 16px;
        padding-bottom: 12px;
        border-bottom: 2px solid #f0f0f5;
    }

    /* ============ 区域评分卡片 ============ */
    .district-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        border: 1px solid #f0f0f5;
        border-left: 4px solid #e2e8f0;
        transition: all 0.25s ease;
        margin-bottom: 12px;
    }
    .district-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        transform: translateX(4px);
    }
    .district-card.score-high { border-left-color: #10b981; }
    .district-card.score-mid { border-left-color: #f59e0b; }
    .district-card.score-low { border-left-color: #ef4444; }

    /* ============ 功能入口卡片 ============ */
    .feature-card {
        background: white;
        border-radius: 16px;
        padding: 28px 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        border: 1px solid #f0f0f5;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .feature-card:hover {
        box-shadow: 0 8px 24px rgba(15,52,96,0.12);
        transform: translateY(-4px);
        border-color: #0f3460;
    }
    .feature-card .icon {
        font-size: 40px;
        margin-bottom: 12px;
    }
    .feature-card h4 {
        margin: 0 0 8px;
        font-size: 16px;
        font-weight: 600;
        color: #1a1a2e;
    }
    .feature-card p {
        margin: 0;
        font-size: 13px;
        color: #94a3b8;
        line-height: 1.5;
    }

    /* ============ 案例卡片 ============ */
    .case-card {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        border: 1px solid #f0f0f5;
        margin-bottom: 10px;
        transition: all 0.2s;
    }
    .case-card:hover { background: #fafbfd; }
    .case-card.profit { border-left: 3px solid #10b981; }
    .case-card.loss { border-left: 3px solid #ef4444; }
    .case-card .case-header {
        font-weight: 600;
        font-size: 14px;
        color: #1a1a2e;
    }
    .case-card .case-result {
        font-weight: 700;
        font-size: 15px;
        margin: 6px 0;
    }
    .case-card .case-detail {
        font-size: 12px;
        color: #94a3b8;
        line-height: 1.5;
    }
    .profit-text { color: #10b981; }
    .loss-text { color: #ef4444; }

    /* ============ 数值高亮 ============ */
    .big-number {
        font-size: 36px;
        font-weight: 700;
        color: #1a1a2e;
        line-height: 1.2;
    }
    .big-number.accent { color: #e94560; }
    .big-number.success { color: #10b981; }

    /* ============ 分割线美化 ============ */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
        margin: 28px 0;
    }

    /* ============ Tabs美化 ============ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #f1f5f9;
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: white !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    /* ============ 按钮美化 ============ */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0f3460, #1a5276);
        border: none;
        border-radius: 10px;
        padding: 8px 32px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #1a5276, #2471a3);
        box-shadow: 0 4px 12px rgba(15,52,96,0.3);
        transform: translateY(-1px);
    }

    /* ============ 动画 ============ */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(16px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-in {
        animation: fadeInUp 0.5s ease-out;
    }

    /* ============ Selectbox美化 ============ */
    .stSelectbox > div > div {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)


def metric_card(icon, label, value, delta=None, delta_color="success"):
    """渲染一个美化的指标卡片"""
    delta_html = ""
    if delta:
        color = COLORS.get(delta_color, "#94a3b8")
        delta_html = f'<div class="metric-delta" style="color:{color}">{delta}</div>'
    return f"""
    <div class="metric-card animate-in">
        <div class="metric-icon">{icon}</div>
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """


def hero_section(title, subtitle=""):
    """渲染hero头部区域"""
    st.markdown(f"""
    <div class="hero-section animate-in">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def score_badge(score):
    """根据分数返回彩色徽章HTML"""
    if score >= 60:
        cls = "green"
    elif score >= 45:
        cls = "yellow"
    elif score >= 30:
        cls = "orange"
    else:
        cls = "red"
    return f'<div class="score-badge {cls}">{score}</div>'


def status_tag(verdict):
    """返回状态标签HTML"""
    tag_map = {
        "强烈推荐买入": ("buy", "强烈推荐"),
        "可以考虑买入": ("buy", "可以考虑"),
        "谨慎观望": ("hold", "谨慎观望"),
        "不建议买入": ("caution", "不建议"),
        "强烈不建议": ("avoid", "强烈避开"),
    }
    cls, text = tag_map.get(verdict, ("hold", verdict))
    return f'<span class="status-tag {cls}">{text}</span>'


def content_card(title, content_html):
    """包裹内容在卡片容器中"""
    st.markdown(f"""
    <div class="content-card animate-in">
        <h3>{title}</h3>
        {content_html}
    </div>
    """, unsafe_allow_html=True)


def district_score_card(district, score, price, yield_pct, verdict, reason):
    """区域评分卡片"""
    if score >= 60:
        cls = "score-high"
    elif score >= 45:
        cls = "score-mid"
    else:
        cls = "score-low"
    tag = status_tag(verdict)
    return f"""
    <div class="district-card {cls} animate-in">
        <div style="display:flex;align-items:center;justify-content:space-between;">
            <div style="flex:1;">
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                    <span style="font-size:18px;font-weight:700;color:#1a1a2e;">{district}</span>
                    {tag}
                </div>
                <div style="display:flex;gap:24px;font-size:13px;color:#64748b;">
                    <span>均价 <b style="color:#1a1a2e;">{price:,}</b> 元/㎡</span>
                    <span>租金回报 <b style="color:#1a1a2e;">{yield_pct}%</b></span>
                </div>
                <div style="font-size:13px;color:#94a3b8;margin-top:6px;">{reason[:50]}...</div>
            </div>
            <div>{score_badge(score)}</div>
        </div>
    </div>
    """


def case_card(sector, community, year, profit, return_pct, story):
    """成交案例卡片"""
    cls = "profit" if profit > 0 else "loss"
    txt_cls = "profit-text" if profit > 0 else "loss-text"
    prefix = "盈利" if profit > 0 else "亏损"
    return f"""
    <div class="case-card {cls}">
        <div class="case-header">{sector} · {community} | {year}年买入</div>
        <div class="case-result {txt_cls}">{prefix} {abs(profit):.1f}万 | 年化 {return_pct}%</div>
        <div class="case-detail">{story}</div>
    </div>
    """


def apply_plotly_style(fig, height=400):
    """统一Plotly图表样式"""
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=height,
    )
    return fig


def get_district_names(city_config, with_hierarchy_prefix=True):
    """从城市配置中提取区域名列表，带层级前缀。
    返回: [(display_name, actual_name), ...]
    display_name 用于 UI 展示，actual_name 用于数据查询。
    """
    districts = city_config.get("districts", [])
    parent_map = {}  # parent_name -> [child dicts]
    top_level = []
    for d in districts:
        if "parent" in d:
            parent_map.setdefault(d["parent"], []).append(d)
        else:
            top_level.append(d)

    result = []
    for d in top_level:
        result.append((d["name"], d["name"]))
        if d["name"] in parent_map:
            for child in parent_map[d["name"]]:
                prefix = "  ↳ " if with_hierarchy_prefix else ""
                result.append((f"{prefix}{child['name']}", child["name"]))
    return result
