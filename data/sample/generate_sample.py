"""生成贴近真实市场的示例数据"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import random
import numpy as np
from core.database import init_db, get_connection

random.seed(42)
np.random.seed(42)

# 各城市各区域的真实价格水平参考（元/㎡，2025年数据）
# 数据来源：安居客、房天下、中国房价行情网、中原地产等平台 2025年挂牌/成交均价
DISTRICT_PROFILES = {
    "北京": {
        # 来源：安居客 2026年2-3月二手房挂牌均价；全市均价约54,000元/㎡
        "朝阳": {"price": 63000, "rent": 95, "land_price": 45000, "build_year_range": (1995, 2022)},
        "海淀": {"price": 82000, "rent": 105, "land_price": 58000, "build_year_range": (1990, 2022)},
        "西城": {"price": 110000, "rent": 120, "land_price": 75000, "build_year_range": (1985, 2015)},
        "东城": {"price": 91000, "rent": 110, "land_price": 62000, "build_year_range": (1985, 2015)},
        "丰台": {"price": 50000, "rent": 70, "land_price": 32000, "build_year_range": (1998, 2023)},
        "通州": {"price": 35000, "rent": 45, "land_price": 20000, "build_year_range": (2005, 2023)},
        "大兴": {"price": 35000, "rent": 45, "land_price": 20000, "build_year_range": (2005, 2023)},
        "昌平": {"price": 32000, "rent": 40, "land_price": 18000, "build_year_range": (2003, 2023)},
    },
    "上海": {
        # 来源：安居客/房天下 2026年2-3月；全市均价约51,750元/㎡
        "浦东": {"price": 52000, "rent": 85, "land_price": 35000, "build_year_range": (1998, 2023)},
        "徐汇": {"price": 70000, "rent": 105, "land_price": 48000, "build_year_range": (1990, 2020)},
        "静安": {"price": 65000, "rent": 98, "land_price": 45000, "build_year_range": (1988, 2018)},
        "黄浦": {"price": 90000, "rent": 125, "land_price": 62000, "build_year_range": (1985, 2015)},
        "长宁": {"price": 63000, "rent": 95, "land_price": 43000, "build_year_range": (1992, 2020)},
        "闵行": {"price": 42000, "rent": 62, "land_price": 26000, "build_year_range": (2000, 2023)},
        "宝山": {"price": 33000, "rent": 48, "land_price": 18000, "build_year_range": (2002, 2023)},
        "松江": {"price": 28000, "rent": 40, "land_price": 15000, "build_year_range": (2005, 2023)},
    },
    "深圳": {
        # 来源：新浪财经 2026年2月，全市二手房均价6.2万/㎡，连续3个月上涨
        "南山": {"price": 86000, "rent": 108, "land_price": 60000, "build_year_range": (1998, 2023)},
        "福田": {"price": 76000, "rent": 98, "land_price": 52000, "build_year_range": (1995, 2022)},
        "罗湖": {"price": 44000, "rent": 60, "land_price": 28000, "build_year_range": (1990, 2018)},
        "宝安": {"price": 48000, "rent": 58, "land_price": 30000, "build_year_range": (2002, 2023)},
        "龙华": {"price": 48000, "rent": 55, "land_price": 28000, "build_year_range": (2005, 2023)},
        "龙岗": {"price": 33000, "rent": 38, "land_price": 16000, "build_year_range": (2005, 2023)},
        "光明": {"price": 30000, "rent": 33, "land_price": 15000, "build_year_range": (2010, 2023)},
    },
    "广州": {
        # 来源：房天下/安居客 2025年1月二手房挂牌均价
        "天河": {"price": 49000, "rent": 75, "land_price": 35000, "build_year_range": (1998, 2023)},
        "越秀": {"price": 51000, "rent": 72, "land_price": 35000, "build_year_range": (1990, 2018)},
        "海珠": {"price": 38000, "rent": 60, "land_price": 25000, "build_year_range": (1995, 2022)},
        "荔湾": {"price": 32000, "rent": 50, "land_price": 20000, "build_year_range": (1988, 2018)},
        "番禺": {"price": 26000, "rent": 38, "land_price": 15000, "build_year_range": (2003, 2023)},
        "白云": {"price": 25000, "rent": 38, "land_price": 14000, "build_year_range": (2000, 2023)},
        "黄埔": {"price": 23000, "rent": 35, "land_price": 13000, "build_year_range": (2005, 2023)},
    },
    "杭州": {
        # 来源：中国房价行情 2026年1月，全市均价32,613元/㎡；房天下/安居客 2026年2月
        "西湖": {"price": 40000, "rent": 58, "land_price": 28000, "build_year_range": (1998, 2022)},
        "拱墅": {"price": 30000, "rent": 45, "land_price": 18000, "build_year_range": (2000, 2023)},
        "上城": {"price": 42000, "rent": 62, "land_price": 30000, "build_year_range": (1995, 2022)},
        "滨江": {"price": 37000, "rent": 55, "land_price": 25000, "build_year_range": (2005, 2023)},
        "余杭": {"price": 22000, "rent": 32, "land_price": 12000, "build_year_range": (2008, 2023)},
        "萧山": {"price": 20000, "rent": 30, "land_price": 11000, "build_year_range": (2005, 2023)},
    },
    "成都": {
        # 来源：知乎"好好选房" 2025年4月成都二手房成交均价
        "锦江": {"price": 19000, "rent": 38, "land_price": 12000, "build_year_range": (1998, 2023)},
        "青羊": {"price": 18000, "rent": 35, "land_price": 11000, "build_year_range": (1998, 2023)},
        "武侯": {"price": 15000, "rent": 32, "land_price": 9000, "build_year_range": (2000, 2023)},
        "高新": {"price": 20000, "rent": 42, "land_price": 13000, "build_year_range": (2005, 2023)},
        "天府新区": {"price": 16000, "rent": 30, "land_price": 9000, "build_year_range": (2012, 2023)},
        "龙泉驿": {"price": 10000, "rent": 18, "land_price": 5000, "build_year_range": (2008, 2023)},
    },
    "福州": {
        # 来源：中国房价行情 2026年1月，全市二手房均价20,726元/㎡；吉屋网/安居客
        "鼓楼": {"price": 30000, "rent": 48, "land_price": 20000, "build_year_range": (1995, 2022)},
        "台江": {"price": 25000, "rent": 40, "land_price": 16000, "build_year_range": (1998, 2022)},
        "仓山": {"price": 18000, "rent": 28, "land_price": 10000, "build_year_range": (2003, 2023)},
        "晋安": {"price": 17000, "rent": 26, "land_price": 9000, "build_year_range": (2005, 2023)},
        "马尾": {"price": 13000, "rent": 18, "land_price": 6000, "build_year_range": (2005, 2023)},
        "长乐": {"price": 10000, "rent": 14, "land_price": 5000, "build_year_range": (2008, 2023)},
        "闽侯": {"price": 12000, "rent": 16, "land_price": 6000, "build_year_range": (2008, 2023)},
    },
    "厦门": {
        # 来源：房天下 2026年3月，思明49,820；安居客/厦门在线 2026年Q1数据
        "思明": {"price": 50000, "rent": 68, "land_price": 38000, "build_year_range": (1995, 2022)},
        "湖里": {"price": 38000, "rent": 52, "land_price": 25000, "build_year_range": (2000, 2023)},
        "集美": {"price": 25000, "rent": 32, "land_price": 14000, "build_year_range": (2005, 2023)},
        "海沧": {"price": 28000, "rent": 35, "land_price": 15000, "build_year_range": (2005, 2023)},
        "同安": {"price": 20000, "rent": 25, "land_price": 10000, "build_year_range": (2008, 2023)},
        "翔安": {"price": 18000, "rent": 22, "land_price": 9000, "build_year_range": (2010, 2023)},
    },
    "泉州": {
        # 来源：吉屋网 2025年1月；安居客/房天下；全市均价约13,000-14,500
        "鲤城": {"price": 20000, "rent": 30, "land_price": 12000, "build_year_range": (1998, 2022)},
        "丰泽": {"price": 17500, "rent": 26, "land_price": 10000, "build_year_range": (2000, 2023)},
        "洛江": {"price": 11000, "rent": 16, "land_price": 5500, "build_year_range": (2005, 2023)},
        "晋江": {"price": 10000, "rent": 16, "land_price": 5000, "build_year_range": (2003, 2023)},
        "石狮": {"price": 8000, "rent": 13, "land_price": 4000, "build_year_range": (2003, 2023)},
        "南安": {"price": 6000, "rent": 10, "land_price": 3000, "build_year_range": (2005, 2023)},
        "安溪": {"price": 9000, "rent": 13, "land_price": 4000, "build_year_range": (2005, 2023)},
    },
    "莆田": {
        # 来源：吉屋网/安居客 2025年；全市均价约14,293
        "城厢": {"price": 16000, "rent": 22, "land_price": 8000, "build_year_range": (2000, 2023)},
        "涵江": {"price": 10000, "rent": 14, "land_price": 5000, "build_year_range": (2003, 2023)},
        "荔城": {"price": 17000, "rent": 23, "land_price": 9000, "build_year_range": (2002, 2023)},
        "秀屿": {"price": 6000, "rent": 9, "land_price": 3000, "build_year_range": (2008, 2023)},
        "仙游": {"price": 7000, "rent": 10, "land_price": 3000, "build_year_range": (2005, 2023)},
    },
    "廊坊": {
        # 来源：安居客/房天下 2025年；全市均价约7,800-8,600
        "广阳": {"price": 8700, "rent": 14, "land_price": 4000, "build_year_range": (2003, 2023)},
        "安次": {"price": 8000, "rent": 12, "land_price": 3500, "build_year_range": (2005, 2023)},
        "霸州": {"price": 7000, "rent": 10, "land_price": 3000, "build_year_range": (2008, 2023)},
        "胜芳": {"price": 4500, "rent": 7, "land_price": 2000, "build_year_range": (2008, 2023)},
        "固安": {"price": 7600, "rent": 11, "land_price": 3500, "build_year_range": (2010, 2023)},
        "香河": {"price": 7000, "rent": 10, "land_price": 3000, "build_year_range": (2010, 2023)},
        "燕郊": {"price": 10000, "rent": 16, "land_price": 5000, "build_year_range": (2005, 2023)},
    },
    "昆明": {
        # 来源：腾讯新闻/房天下 2026年1月；全市二手房均价约9,500
        "五华": {"price": 13000, "rent": 25, "land_price": 7000, "build_year_range": (1998, 2023)},
        "盘龙": {"price": 11000, "rent": 22, "land_price": 6000, "build_year_range": (2000, 2023)},
        "官渡": {"price": 9000, "rent": 18, "land_price": 5000, "build_year_range": (2002, 2023)},
        "西山": {"price": 11000, "rent": 22, "land_price": 6000, "build_year_range": (2000, 2023)},
        "呈贡": {"price": 8000, "rent": 15, "land_price": 4000, "build_year_range": (2010, 2023)},
        "晋宁": {"price": 5500, "rent": 10, "land_price": 2500, "build_year_range": (2012, 2023)},
    },
    "大理": {
        # 来源：吉屋网/链家/房天下 2025年；全市均价约10,000-11,700
        # 古城旅居市场，下关刚需市场，海东高端观海
        "大理古城": {"price": 15000, "rent": 42, "land_price": 8000, "build_year_range": (2005, 2023)},
        "下关": {"price": 8500, "rent": 18, "land_price": 4500, "build_year_range": (2000, 2023)},
        "海东": {"price": 10000, "rent": 20, "land_price": 5000, "build_year_range": (2012, 2023)},
        "凤仪": {"price": 5000, "rent": 10, "land_price": 2500, "build_year_range": (2010, 2023)},
        "喜洲": {"price": 10000, "rent": 32, "land_price": 5000, "build_year_range": (2008, 2023)},
        "双廊": {"price": 12000, "rent": 38, "land_price": 6000, "build_year_range": (2010, 2023)},
        "银桥": {"price": 8000, "rent": 25, "land_price": 4000, "build_year_range": (2012, 2023)},
        "湾桥": {"price": 7000, "rent": 20, "land_price": 3500, "build_year_range": (2012, 2023)},
        "挖色": {"price": 9000, "rent": 28, "land_price": 4500, "build_year_range": (2013, 2023)},
    },
    "丽江": {
        # 来源：安居客/房天下 2025年；全市均价约8,411；古城区约10,363
        "古城区": {"price": 10000, "rent": 28, "land_price": 5000, "build_year_range": (2005, 2023)},
        "束河": {"price": 8000, "rent": 25, "land_price": 4000, "build_year_range": (2008, 2023)},
        "玉龙": {"price": 6500, "rent": 13, "land_price": 3000, "build_year_range": (2010, 2023)},
    },
    "曲靖": {
        # 来源：中国房价行情 2025年11月；全市均价约5,500-6,500
        "麒麟": {"price": 6500, "rent": 13, "land_price": 3000, "build_year_range": (2003, 2023)},
        "沾益": {"price": 4500, "rent": 8, "land_price": 2000, "build_year_range": (2008, 2023)},
        "马龙": {"price": 3500, "rent": 6, "land_price": 1500, "build_year_range": (2010, 2023)},
    },
    "玉溪": {
        # 来源：中国房价行情 2025年12月；安居客；全市均价约6,000-7,000
        "红塔": {"price": 7000, "rent": 14, "land_price": 3500, "build_year_range": (2003, 2023)},
        "江川": {"price": 4500, "rent": 8, "land_price": 2000, "build_year_range": (2008, 2023)},
        "澄江": {"price": 6500, "rent": 15, "land_price": 3000, "build_year_range": (2010, 2023)},
    },
}

# 历史价格系数（相对于当前价格的倍数）
# 一线城市2016-2017大涨后回落，2021短暂反弹后持续下跌
# 二三线城市2018-2019棚改高峰后持续回落
# 数据基于国家统计局70城房价指数及各城市实际走势拟合
HISTORICAL_PRICE_INDEX_TIER1 = {  # 一线城市（北上广深）
    2010: 0.45, 2011: 0.50, 2012: 0.50, 2013: 0.55,
    2014: 0.55, 2015: 0.60, 2016: 0.80, 2017: 1.00,
    2018: 1.05, 2019: 1.08, 2020: 1.05, 2021: 1.15,
    2022: 1.10, 2023: 1.05, 2024: 1.00, 2025: 0.95, 2026: 0.93,
}
HISTORICAL_PRICE_INDEX_TIER15 = {  # 新一线（杭州、成都、厦门）
    2010: 0.40, 2011: 0.45, 2012: 0.45, 2013: 0.50,
    2014: 0.52, 2015: 0.55, 2016: 0.68, 2017: 0.85,
    2018: 0.95, 2019: 1.00, 2020: 0.98, 2021: 1.10,
    2022: 1.05, 2023: 1.00, 2024: 0.95, 2025: 0.90, 2026: 0.88,
}
HISTORICAL_PRICE_INDEX_TIER2 = {  # 二线（福州、泉州、昆明等）
    2010: 0.50, 2011: 0.55, 2012: 0.55, 2013: 0.58,
    2014: 0.58, 2015: 0.60, 2016: 0.65, 2017: 0.75,
    2018: 0.90, 2019: 1.00, 2020: 1.00, 2021: 1.08,
    2022: 1.02, 2023: 0.98, 2024: 0.92, 2025: 0.88, 2026: 0.85,
}
HISTORICAL_PRICE_INDEX_TIER3 = {  # 三四线（莆田、廊坊、丽江、曲靖、玉溪等）
    2010: 0.55, 2011: 0.60, 2012: 0.60, 2013: 0.62,
    2014: 0.62, 2015: 0.65, 2016: 0.70, 2017: 0.82,
    2018: 1.00, 2019: 1.10, 2020: 1.05, 2021: 1.08,
    2022: 1.00, 2023: 0.95, 2024: 0.88, 2025: 0.82, 2026: 0.78,
}

# 城市到价格指数的映射
CITY_TIER_MAP = {
    "北京": "tier1", "上海": "tier1", "深圳": "tier1", "广州": "tier1",
    "杭州": "tier15", "成都": "tier15", "厦门": "tier15",
    "福州": "tier2", "泉州": "tier2", "昆明": "tier2", "大理": "tier2",
    "莆田": "tier3", "廊坊": "tier3", "丽江": "tier3",
    "曲靖": "tier3", "玉溪": "tier3",
}

def get_price_index(city):
    """获取城市对应的历史价格指数"""
    tier = CITY_TIER_MAP.get(city, "tier3")
    if tier == "tier1":
        return HISTORICAL_PRICE_INDEX_TIER1
    elif tier == "tier15":
        return HISTORICAL_PRICE_INDEX_TIER15
    elif tier == "tier2":
        return HISTORICAL_PRICE_INDEX_TIER2
    else:
        return HISTORICAL_PRICE_INDEX_TIER3

# 宏观数据参考（人口万人、GDP亿元、人均可支配收入元）
# 数据来源：各市2024年统计公报/国民经济和社会发展统计公报
MACRO_PROFILES = {
    "北京": {"pop": 2185, "gdp": 46760, "income": 85000, "gdp_g": 0.052},
    "上海": {"pop": 2487, "gdp": 49800, "income": 87000, "gdp_g": 0.050},
    "深圳": {"pop": 1779, "gdp": 36800, "income": 78000, "gdp_g": 0.055},
    "广州": {"pop": 1882, "gdp": 31600, "income": 76000, "gdp_g": 0.048},
    "杭州": {"pop": 1252, "gdp": 21200, "income": 75000, "gdp_g": 0.052},
    "成都": {"pop": 2140, "gdp": 23800, "income": 54000, "gdp_g": 0.058},
    "福州": {"pop": 845, "gdp": 13500, "income": 53000, "gdp_g": 0.048},
    "厦门": {"pop": 535, "gdp": 8600, "income": 68000, "gdp_g": 0.050},
    "泉州": {"pop": 888, "gdp": 12800, "income": 49000, "gdp_g": 0.045},
    "莆田": {"pop": 322, "gdp": 3350, "income": 41000, "gdp_g": 0.042},
    "廊坊": {"pop": 546, "gdp": 3800, "income": 38000, "gdp_g": 0.035},
    "昆明": {"pop": 860, "gdp": 8200, "income": 49000, "gdp_g": 0.042},
    "大理": {"pop": 133, "gdp": 1900, "income": 36000, "gdp_g": 0.038},
    "丽江": {"pop": 55, "gdp": 650, "income": 33000, "gdp_g": 0.035},
    "曲靖": {"pop": 580, "gdp": 4100, "income": 39000, "gdp_g": 0.048},
    "玉溪": {"pop": 230, "gdp": 2600, "income": 41000, "gdp_g": 0.040},
}

# 板块数据：每个区域下的具体板块
DISTRICT_SECTORS = {
    "北京": {
        "朝阳": ["望京", "CBD", "朝青", "常营", "双井", "亚运村", "北苑"],
        "海淀": ["中关村", "五道口", "西二旗", "上地", "清河", "万柳"],
        "西城": ["金融街", "西单", "德胜门", "广安门", "陶然亭"],
        "东城": ["东直门", "王府井", "崇文门", "和平里"],
        "丰台": ["丽泽", "科技园", "宋家庄", "方庄", "花乡"],
        "通州": ["通州核心", "运河商务区", "梨园", "台湖"],
        "大兴": ["亦庄", "黄村", "旧宫", "西红门"],
        "昌平": ["回龙观", "天通苑", "沙河", "昌平新城"],
    },
    "上海": {
        "浦东": ["陆家嘴", "张江", "金桥", "花木", "唐镇", "三林"],
        "徐汇": ["徐家汇", "衡山路", "田林", "漕河泾"],
        "静安": ["南京西路", "曹家渡", "大宁", "彭浦"],
        "黄浦": ["人民广场", "新天地", "老西门", "董家渡"],
        "长宁": ["古北", "中山公园", "虹桥", "天山"],
        "闵行": ["莘庄", "七宝", "浦江", "颛桥"],
        "宝山": ["大华", "顾村", "共富", "淞南"],
        "松江": ["松江新城", "九亭", "泗泾", "佘山"],
    },
    "深圳": {
        "南山": ["科技园", "蛇口", "后海", "前海", "西丽"],
        "福田": ["香蜜湖", "车公庙", "景田", "梅林", "华强北"],
        "罗湖": ["东门", "翠竹", "笋岗", "布心"],
        "宝安": ["西乡", "沙井", "松岗", "新安"],
        "龙华": ["红山", "民治", "龙华中心", "观澜"],
        "龙岗": ["坂田", "布吉", "大运", "龙城"],
        "光明": ["光明中心", "公明", "凤凰"],
    },
    "广州": {
        "天河": ["珠江新城", "天河北", "东圃", "棠下", "员村"],
        "越秀": ["东山口", "北京路", "淘金", "环市东"],
        "海珠": ["滨江", "客村", "赤岗", "琶洲"],
        "荔湾": ["西关", "白鹅潭", "芳村", "花地湾"],
        "番禺": ["万博", "市桥", "大学城", "华南板块"],
        "白云": ["白云新城", "同德围", "金沙洲", "嘉禾望岗"],
        "黄埔": {"科学城", "知识城", "鱼珠", "大沙地"},
    },
    "杭州": {
        "西湖": ["文教区", "三墩", "转塘", "之江"],
        "拱墅": ["武林", "申花", "桥西", "半山"],
        "上城": ["钱江新城", "南星", "采荷", "凯旋"],
        "滨江": ["滨江核心", "长河", "浦沿", "西兴"],
        "余杭": ["未来科技城", "良渚", "临平", "闲林"],
        "萧山": ["市北", "钱江世纪城", "城厢", "宁围"],
    },
    "成都": {
        "锦江": ["攀成钢", "东大街", "三圣乡", "牛市口"],
        "青羊": ["宽窄巷", "金沙", "光华", "苏坡"],
        "武侯": ["桐梓林", "红牌楼", "簇桥", "大源"],
        "高新": ["金融城", "大源", "中和", "新川"],
        "天府新区": ["麓湖", "华阳", "天府中心", "锦江生态带"],
        "龙泉驿": ["大面", "十陵", "洪河", "龙泉中心"],
    },
    "福州": {
        "鼓楼": ["五四路", "温泉", "华林", "洪山", "鼓东"],
        "台江": ["万达", "苍霞", "新港", "茶亭"],
        "仓山": ["金山", "建新", "盖山", "城门"],
        "晋安": ["王庄", "东二环", "岳峰", "鼓山"],
        "马尾": ["马尾中心", "快安", "琅岐"],
        "长乐": ["航城", "吴航", "营前"],
        "闽侯": ["大学城", "甘蔗", "南屿", "上街"],
    },
    "厦门": {
        "思明": ["鹭江", "莲前", "筼筜湖", "前埔", "会展中心"],
        "湖里": ["五缘湾", "金山", "枋湖", "殿前"],
        "集美": ["集美新城", "杏林", "软件园三期", "灌口"],
        "海沧": ["海沧中心", "新阳", "马銮湾"],
        "同安": ["同安老城", "环东海域", "同安工业区"],
        "翔安": ["翔安新城", "马巷", "新店"],
    },
    "泉州": {
        "鲤城": ["西街", "浮桥", "江南", "开元"],
        "丰泽": ["东海", "城东", "北峰", "丰泽新村"],
        "洛江": ["万安", "双阳", "河市"],
        "晋江": ["青阳", "梅岭", "池店", "安海"],
        "石狮": {"石狮城区", "宝盖", "蚶江"},
        "南安": ["水头", "溪美", "官桥"],
        "安溪": ["凤城", "城厢", "参内", "龙门"],
    },
    "莆田": {
        "城厢": ["文献路", "霞林", "龙桥", "华亭"],
        "涵江": ["涵东", "涵西", "白塘", "三江口"],
        "荔城": ["镇海", "拱辰", "新度", "北高"],
        "秀屿": ["笏石", "东庄", "埭头"],
        "仙游": ["鲤城街道", "榜头", "枫亭", "大济"],
    },
    "廊坊": {
        "广阳": ["万达商圈", "银河北路", "新华路", "爱民道"],
        "安次": ["光明西道", "永华道", "龙河高新区"],
        "霸州": ["霸州城区", "煎茶铺", "杨芬港", "信安"],
        "胜芳": ["胜芳镇中心", "红星街", "崔庄子", "堂二里"],
        "固安": ["固安新城", "永定城", "大卫城", "孔雀城"],
        "香河": ["香河新城", "安平", "淑阳", "五百户"],
        "燕郊": ["燕顺路", "迎宾路", "燕郊南城", "燕郊北部新区"],
    },
    "昆明": {
        "五华": ["翠湖", "北市区", "西站", "龙泉路", "学府路"],
        "盘龙": ["白塔路", "北京路", "东风广场", "世博片区", "金殿"],
        "官渡": ["世纪城", "新螺蛳湾", "官渡古镇", "巫家坝"],
        "西山": ["滇池路", "前卫", "马街", "碧鸡"],
        "呈贡": ["大学城", "乌龙", "洛龙", "雨花"],
        "晋宁": ["昆阳", "晋城", "古城"],
    },
    "大理": {
        # 大理高精度：每个区域细分到具体位置
        "大理古城": ["人民路", "洋人街", "玉洱路", "苍山门", "南门", "三月街",
                     "才村", "龙龛", "大理大学周边"],
        "下关": ["泰安路", "建设路", "苍山路", "龙溪路", "满江", "大关邑",
                 "金星", "荷花", "下关北", "经开区"],
        "海东": ["海东新城", "天镜阁", "金梭岛周边", "海东山地", "向阳"],
        "凤仪": ["凤仪镇中心", "华营", "凤鸣路"],
        "喜洲": ["喜洲古镇", "桃源", "周城", "蝴蝶泉"],
        "双廊": ["双廊古镇", "玉几岛", "南诏风情岛", "大建旁"],
        "银桥": ["银桥镇中心", "磻溪", "阳波"],
        "湾桥": ["湾桥镇中心", "上阳溪", "甸中"],
        "挖色": ["挖色镇中心", "小普陀", "康廊"],
    },
    "丽江": {
        "古城区": ["大研古城", "束河路", "祥和", "福慧路", "金甲"],
        "束河": ["束河古镇", "白沙", "龙泉"],
        "玉龙": ["黄山镇", "拉市海", "白沙镇"],
    },
    "曲靖": {
        "麒麟": ["南宁路", "麒麟花园", "珠江源", "翠峰"],
        "沾益": ["沾益城区", "花山", "白水"],
        "马龙": ["马龙城区", "通泉"],
    },
    "玉溪": {
        "红塔": ["聂耳路", "东风路", "高仓", "玉兴路"],
        "江川": ["大街", "星云湖畔", "前卫"],
        "澄江": ["澄江城区", "抚仙湖畔", "右所"],
    },
}

def generate_all():
    init_db()
    with get_connection() as conn:
        for city, districts in DISTRICT_PROFILES.items():
            for district, profile in districts.items():
                # 生成区域统计快照（从2015年开始，覆盖完整历史周期）
                for year in range(2015, 2027):
                    for month in range(1, 13):
                        if year == 2026 and month > 3:
                            break
                        month_str = f"{year}-{month:02d}"
                        district_price_index = get_price_index(city)
                        price_idx = district_price_index.get(year, 0.90)
                        # 月度微调
                        monthly_noise = random.gauss(1.0, 0.02)
                        avg_price = round(profile["price"] * price_idx * monthly_noise)
                        median_price = round(avg_price * random.uniform(0.95, 1.02))
                        txn_count = random.randint(20, 200)
                        avg_rent = round(profile["rent"] * random.gauss(1.0, 0.05), 1)
                        rtp = round(avg_rent * 12 / avg_price, 6) if avg_price > 0 else 0
                        listing_count = random.randint(50, 500)
                        avg_cycle = random.randint(60, 150)

                        conn.execute("""
                            INSERT OR IGNORE INTO district_stats
                            (city, district, month, avg_unit_price, median_unit_price,
                             transaction_count, avg_rent_per_sqm, rent_to_price_ratio,
                             listing_count, avg_deal_cycle)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (city, district, month_str, avg_price, median_price,
                              txn_count, avg_rent, rtp, listing_count, avg_cycle))

                # 土地出让数据
                for year in range(2019, 2026):
                    n_sales = random.randint(1, 5)
                    for _ in range(n_sales):
                        land_area = round(random.uniform(5000, 100000), 0)
                        far = round(random.uniform(1.5, 4.0), 1)
                        floor_price = round(profile["land_price"] * random.gauss(1.0, 0.2))
                        total = round(floor_price * land_area * far / 100000000, 2)
                        month = random.randint(1, 12)
                        sale_date = f"{year}-{month:02d}-{random.randint(1,28):02d}"

                        conn.execute("""
                            INSERT INTO land_sales
                            (city, district, land_area, floor_area_ratio, floor_price,
                             total_price, sale_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (city, district, land_area, far, floor_price, total, sale_date))

            # 宏观数据
            mp = MACRO_PROFILES[city]
            for year in range(2018, 2027):
                yr_offset = year - 2024
                pop = round(mp["pop"] * (1 + 0.005 * yr_offset), 1)
                gdp = round(mp["gdp"] * (1 + mp["gdp_g"]) ** yr_offset, 1)
                income = round(mp["income"] * (1 + 0.05) ** yr_offset)

                conn.execute("""
                    INSERT OR IGNORE INTO macro_data
                    (city, year, population, gdp, disposable_income, gdp_growth, income_growth, cpi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (city, year, pop, gdp, income,
                      round(mp["gdp_g"] + random.gauss(0, 0.01), 3),
                      round(0.05 + random.gauss(0, 0.01), 3),
                      round(1.02 + random.gauss(0, 0.005), 3)))

        # 板块数据（真实板块名称，价格由区域均价推算）
        for city, districts in DISTRICT_SECTORS.items():
            if city not in DISTRICT_PROFILES:
                continue
            for district, sectors in districts.items():
                if district not in DISTRICT_PROFILES.get(city, {}):
                    continue
                profile = DISTRICT_PROFILES[city][district]
                sector_list = list(sectors) if isinstance(sectors, (set, list)) else sectors

                for i, sector in enumerate(sector_list):
                    # 板块价格有差异：第一个板块通常最贵
                    sector_factor = 1.15 - i * 0.08 + random.gauss(0, 0.03)
                    sector_factor = max(0.7, min(1.3, sector_factor))
                    s_price = round(profile["price"] * sector_factor)
                    s_rent = round(profile["rent"] * sector_factor, 1)
                    n_comm = random.randint(5, 30)

                    conn.execute("""
                        INSERT OR IGNORE INTO sectors
                        (city, district, sector_name, avg_unit_price, avg_rent_per_sqm,
                         community_count, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (city, district, sector, s_price, s_rent, n_comm, ""))

    print("示例数据生成完成！")


if __name__ == "__main__":
    generate_all()
