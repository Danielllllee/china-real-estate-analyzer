"""房价走势总览 — 暂无真实历史数据"""
import streamlit as st
import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from core.styles import inject_global_css, hero_section
st.set_page_config(page_title="房价走势", page_icon="📈", layout="wide")
inject_global_css()
hero_section("房价走势总览", "各城市房价历史趋势")
st.info("房价走势图需要真实的历史价格数据才能展示。目前仅有当前时点的区域均价数据，尚无经过核实的历史走势数据，该功能暂不可用。")
