"""中国房产估值与收益率分析系统 - 主入口"""
import streamlit as st
import os
import sys
import yaml

# 确保项目根目录在 path 中
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.database import init_db, get_db_path

st.set_page_config(
    page_title="房产估值分析系统",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
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

st.title("中国房产估值与收益率分析系统")
st.markdown("---")

st.markdown("""
### 系统功能

本系统从**第一性原理**出发，提供学术级别的房产估值和投资回报分析：

**四大估值模型**
- **租金收益率法** — 房产作为现金流资产的合理定价
- **可比交易法** — 基于真实成交数据的市场定价
- **现金流折现（DCF）** — 未来租金收入的现值估算
- **成本法** — 土地+建造的重置成本底线

**投资分析**
- 全面的买入成本和持有成本计算
- 预期收益率（含IRR）分析
- 历史不同时期买入者的实际回报对比
- 跨城市、跨区域的性价比排名

---
""")

# 快速概览
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("覆盖城市", f"{len(config['cities'])} 个")
with col2:
    total_districts = sum(len(c["districts"]) for c in config["cities"].values())
    st.metric("覆盖区域", f"{total_districts} 个")
with col3:
    st.metric("估值模型", "4 个")

st.markdown("---")
st.markdown("👈 **请在左侧菜单选择功能页面开始分析**")

# 支持的城市列表
st.subheader("支持的城市")
for key, city_info in config["cities"].items():
    districts = "、".join(d["name"] for d in city_info["districts"])
    st.markdown(f"**{city_info['name']}**：{districts}")
