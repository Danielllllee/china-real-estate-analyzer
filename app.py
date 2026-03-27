"""中国房产估值与收益率分析系统 - 主入口"""
import streamlit as st
import os
import sys
import yaml

# 确保项目根目录在 path 中
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.database import init_db, get_db_path
from core.styles import inject_global_css, hero_section, metric_card

st.set_page_config(
    page_title="房产估值分析系统",
    page_icon="\U0001f3db",
    layout="wide",
)

# 初始化数据库
if not os.path.exists(get_db_path()):
    with st.spinner("首次运行，正在初始化数据库和生成示例数据..."):
        init_db()
        from data.sample.generate_sample import generate_all
        generate_all()
        st.success("数据初始化完成！")
else:
    init_db()

# 加载配置
@st.cache_data
def load_config():
    with open(os.path.join(ROOT, "config.yaml"), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()
total_districts = sum(len(c["districts"]) for c in config["cities"].values())

# ============ 全局样式 ============
inject_global_css()

# ============ Hero 区域 ============
hero_section(
    "中国房产估值与收益率分析系统",
    f"从第一性原理出发，覆盖{len(config['cities'])}个城市的学术级房产投资分析平台 | 数据更新至2026年3月",
)

# ============ 核心指标卡片 ============
cols = st.columns(4)
with cols[0]:
    st.markdown(metric_card("\U0001f4ca", "覆盖城市", f"{len(config['cities'])} 个"), unsafe_allow_html=True)
with cols[1]:
    st.markdown(metric_card("\U0001f3d8", "覆盖区域", f"{total_districts} 个"), unsafe_allow_html=True)
with cols[2]:
    st.markdown(metric_card("\U0001f9ee", "估值模型", "4 个"), unsafe_allow_html=True)
with cols[3]:
    st.markdown(metric_card("\U0001f4c8", "数据截至", "2026年3月"), unsafe_allow_html=True)

# ============ 功能导航 ============
st.markdown("---")
st.markdown("### 功能导航")

features = [
    ("\U0001f3d9", "城市概览", "各区域房价、租售比、投资评分一览"),
    ("\U0001f4ca", "区域分析", "深度解读：是否值得买？具体板块推荐"),
    ("\U0001f9ee", "估值计算器", "四大模型综合估值，输入即出结果"),
    ("\U0001f4c8", "收益率分析", "历史回报率、IRR、全成本计算"),
    ("\U0001f30f", "城市对比", "多城市横向对比，找到性价比之王"),
]

feat_cols = st.columns(5)
for i, (icon, title, desc) in enumerate(features):
    with feat_cols[i]:
        st.markdown(f"""
        <div class="feature-card animate-in">
            <div class="icon">{icon}</div>
            <h4>{title}</h4>
            <p>{desc}</p>
        </div>
        """, unsafe_allow_html=True)

# ============ 支持的城市 ============
st.markdown("---")
st.markdown("### 支持的城市")

city_items = list(config["cities"].items())
grid_cols = st.columns(3)
for idx, (key, city_info) in enumerate(city_items):
    with grid_cols[idx % 3]:
        # Build hierarchical district display
        parent_map = {}  # parent_name -> [child_names]
        top_level = []
        for d in city_info["districts"]:
            if "parent" in d:
                parent_map.setdefault(d["parent"], []).append(d["name"])
            else:
                top_level.append(d["name"])
        district_parts = []
        for name in top_level:
            district_parts.append(name)
            if name in parent_map:
                for child in parent_map[name]:
                    district_parts.append(f'<span style="color:#0f3460;font-weight:500;">↳{child}</span>')
        districts_html = "、".join(district_parts)
        st.markdown(f"""
        <div class="content-card" style="min-height:80px;">
            <h3 style="margin-bottom:8px;border:none;padding:0;">{city_info['name']}</h3>
            <p style="font-size:13px;color:#64748b;margin:0;line-height:1.6;">{districts_html}</p>
        </div>
        """, unsafe_allow_html=True)
