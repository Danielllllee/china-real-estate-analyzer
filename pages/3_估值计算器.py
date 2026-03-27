"""估值计算器 — 暂无真实数据支撑"""
import streamlit as st
import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from core.styles import inject_global_css, hero_section
st.set_page_config(page_title="估值计算器", page_icon="🧮", layout="wide")
inject_global_css()
hero_section("估值计算器", "综合估值分析")
st.info("估值计算器需要真实的租金数据、成交数据和土地出让数据才能运行。目前这些数据尚未接入真实数据源，该功能暂不可用。")
