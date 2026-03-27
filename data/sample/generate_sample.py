"""生成贴近真实市场的示例数据"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import random
import numpy as np
from datetime import datetime, timedelta
from utils.database import init_db, get_connection

random.seed(42)
np.random.seed(42)

# 各城市各区域的真实价格水平参考（元/㎡，2024年左右）
DISTRICT_PROFILES = {
    "北京": {
        "朝阳": {"price": 65000, "rent": 110, "land_price": 45000, "build_year_range": (1995, 2022)},
        "海淀": {"price": 80000, "rent": 120, "land_price": 55000, "build_year_range": (1990, 2022)},
        "西城": {"price": 95000, "rent": 130, "land_price": 65000, "build_year_range": (1985, 2015)},
        "东城": {"price": 90000, "rent": 125, "land_price": 60000, "build_year_range": (1985, 2015)},
        "丰台": {"price": 52000, "rent": 85, "land_price": 35000, "build_year_range": (1998, 2023)},
        "通州": {"price": 38000, "rent": 55, "land_price": 22000, "build_year_range": (2005, 2023)},
        "大兴": {"price": 40000, "rent": 58, "land_price": 25000, "build_year_range": (2005, 2023)},
        "昌平": {"price": 35000, "rent": 50, "land_price": 20000, "build_year_range": (2003, 2023)},
    },
    "上海": {
        "浦东": {"price": 62000, "rent": 105, "land_price": 42000, "build_year_range": (1998, 2023)},
        "徐汇": {"price": 85000, "rent": 130, "land_price": 58000, "build_year_range": (1990, 2020)},
        "静安": {"price": 90000, "rent": 135, "land_price": 62000, "build_year_range": (1988, 2018)},
        "黄浦": {"price": 95000, "rent": 140, "land_price": 65000, "build_year_range": (1985, 2015)},
        "长宁": {"price": 78000, "rent": 120, "land_price": 52000, "build_year_range": (1992, 2020)},
        "闵行": {"price": 55000, "rent": 80, "land_price": 35000, "build_year_range": (2000, 2023)},
        "宝山": {"price": 42000, "rent": 60, "land_price": 25000, "build_year_range": (2002, 2023)},
        "松江": {"price": 35000, "rent": 48, "land_price": 18000, "build_year_range": (2005, 2023)},
    },
    "深圳": {
        "南山": {"price": 95000, "rent": 130, "land_price": 65000, "build_year_range": (1998, 2023)},
        "福田": {"price": 85000, "rent": 120, "land_price": 58000, "build_year_range": (1995, 2022)},
        "罗湖": {"price": 50000, "rent": 75, "land_price": 30000, "build_year_range": (1990, 2018)},
        "宝安": {"price": 55000, "rent": 70, "land_price": 32000, "build_year_range": (2002, 2023)},
        "龙华": {"price": 52000, "rent": 65, "land_price": 30000, "build_year_range": (2005, 2023)},
        "龙岗": {"price": 35000, "rent": 45, "land_price": 18000, "build_year_range": (2005, 2023)},
        "光明": {"price": 38000, "rent": 42, "land_price": 20000, "build_year_range": (2010, 2023)},
    },
    "广州": {
        "天河": {"price": 55000, "rent": 85, "land_price": 38000, "build_year_range": (1998, 2023)},
        "越秀": {"price": 52000, "rent": 80, "land_price": 35000, "build_year_range": (1990, 2018)},
        "海珠": {"price": 45000, "rent": 70, "land_price": 30000, "build_year_range": (1995, 2022)},
        "荔湾": {"price": 38000, "rent": 60, "land_price": 25000, "build_year_range": (1988, 2018)},
        "番禺": {"price": 30000, "rent": 45, "land_price": 18000, "build_year_range": (2003, 2023)},
        "白云": {"price": 32000, "rent": 48, "land_price": 20000, "build_year_range": (2000, 2023)},
        "黄埔": {"price": 35000, "rent": 50, "land_price": 22000, "build_year_range": (2005, 2023)},
    },
    "杭州": {
        "西湖": {"price": 55000, "rent": 80, "land_price": 38000, "build_year_range": (1998, 2022)},
        "拱墅": {"price": 42000, "rent": 65, "land_price": 28000, "build_year_range": (2000, 2023)},
        "上城": {"price": 48000, "rent": 72, "land_price": 32000, "build_year_range": (1995, 2022)},
        "滨江": {"price": 45000, "rent": 68, "land_price": 30000, "build_year_range": (2005, 2023)},
        "余杭": {"price": 28000, "rent": 40, "land_price": 15000, "build_year_range": (2008, 2023)},
        "萧山": {"price": 25000, "rent": 38, "land_price": 13000, "build_year_range": (2005, 2023)},
    },
    "成都": {
        "锦江": {"price": 25000, "rent": 45, "land_price": 15000, "build_year_range": (1998, 2023)},
        "青羊": {"price": 22000, "rent": 40, "land_price": 13000, "build_year_range": (1998, 2023)},
        "武侯": {"price": 22000, "rent": 40, "land_price": 13000, "build_year_range": (2000, 2023)},
        "高新": {"price": 28000, "rent": 50, "land_price": 18000, "build_year_range": (2005, 2023)},
        "天府新区": {"price": 20000, "rent": 35, "land_price": 12000, "build_year_range": (2012, 2023)},
        "龙泉驿": {"price": 13000, "rent": 22, "land_price": 7000, "build_year_range": (2008, 2023)},
    },
    "福州": {
        "鼓楼": {"price": 32000, "rent": 52, "land_price": 22000, "build_year_range": (1995, 2022)},
        "台江": {"price": 28000, "rent": 45, "land_price": 18000, "build_year_range": (1998, 2022)},
        "仓山": {"price": 22000, "rent": 35, "land_price": 14000, "build_year_range": (2003, 2023)},
        "晋安": {"price": 20000, "rent": 30, "land_price": 12000, "build_year_range": (2005, 2023)},
        "马尾": {"price": 15000, "rent": 22, "land_price": 8000, "build_year_range": (2005, 2023)},
        "长乐": {"price": 12000, "rent": 18, "land_price": 6000, "build_year_range": (2008, 2023)},
        "闽侯": {"price": 14000, "rent": 20, "land_price": 7000, "build_year_range": (2008, 2023)},
    },
    "厦门": {
        "思明": {"price": 55000, "rent": 75, "land_price": 40000, "build_year_range": (1995, 2022)},
        "湖里": {"price": 42000, "rent": 58, "land_price": 28000, "build_year_range": (2000, 2023)},
        "集美": {"price": 25000, "rent": 35, "land_price": 15000, "build_year_range": (2005, 2023)},
        "海沧": {"price": 23000, "rent": 32, "land_price": 13000, "build_year_range": (2005, 2023)},
        "同安": {"price": 16000, "rent": 22, "land_price": 8000, "build_year_range": (2008, 2023)},
        "翔安": {"price": 18000, "rent": 24, "land_price": 10000, "build_year_range": (2010, 2023)},
    },
    "泉州": {
        "鲤城": {"price": 18000, "rent": 28, "land_price": 10000, "build_year_range": (1998, 2022)},
        "丰泽": {"price": 16000, "rent": 25, "land_price": 9000, "build_year_range": (2000, 2023)},
        "洛江": {"price": 11000, "rent": 18, "land_price": 6000, "build_year_range": (2005, 2023)},
        "晋江": {"price": 14000, "rent": 22, "land_price": 8000, "build_year_range": (2003, 2023)},
        "石狮": {"price": 12000, "rent": 20, "land_price": 7000, "build_year_range": (2003, 2023)},
        "南安": {"price": 10000, "rent": 16, "land_price": 5000, "build_year_range": (2005, 2023)},
    },
}

# 历史价格系数（相对于当前价格的倍数）
# 模拟中国房地产历史走势
HISTORICAL_PRICE_INDEX = {
    2015: 0.55,
    2016: 0.65,
    2017: 0.80,
    2018: 0.88,
    2019: 0.92,
    2020: 0.90,
    2021: 1.05,
    2022: 0.98,
    2023: 0.95,
    2024: 0.92,
    2025: 0.90,
}

# 宏观数据参考
MACRO_PROFILES = {
    "北京": {"pop": 2189, "gdp": 43760, "income": 81752, "gdp_g": 0.052},
    "上海": {"pop": 2489, "gdp": 47218, "income": 84034, "gdp_g": 0.050},
    "深圳": {"pop": 1768, "gdp": 34606, "income": 76910, "gdp_g": 0.060},
    "广州": {"pop": 1882, "gdp": 30355, "income": 74416, "gdp_g": 0.048},
    "杭州": {"pop": 1237, "gdp": 20059, "income": 73826, "gdp_g": 0.055},
    "成都": {"pop": 2127, "gdp": 22074, "income": 52633, "gdp_g": 0.060},
    "福州": {"pop": 845, "gdp": 12928, "income": 52000, "gdp_g": 0.048},
    "厦门": {"pop": 532, "gdp": 8066, "income": 67000, "gdp_g": 0.052},
    "泉州": {"pop": 888, "gdp": 12102, "income": 48000, "gdp_g": 0.045},
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
    },
}


COMMUNITY_NAME_PARTS = [
    ["阳光", "翠苑", "金色", "绿城", "万科", "保利", "中海", "华润", "融创", "龙湖",
     "碧桂", "恒大", "远洋", "首开", "招商", "金地", "世茂", "新城", "旭辉", "绿地"],
    ["花园", "雅苑", "家园", "公馆", "华庭", "新城", "嘉园", "名苑", "豪庭", "美景",
     "府邸", "天下", "国际", "广场", "中心", "壹号", "御苑", "锦苑", "丽景", "雅居"],
]


def random_community_name():
    return random.choice(COMMUNITY_NAME_PARTS[0]) + random.choice(COMMUNITY_NAME_PARTS[1])


def generate_all():
    init_db()
    with get_connection() as conn:
        community_id = 0
        for city, districts in DISTRICT_PROFILES.items():
            for district, profile in districts.items():
                # 每个区域生成10-20个小区
                n_communities = random.randint(10, 20)
                for _ in range(n_communities):
                    community_id += 1
                    name = random_community_name() + str(random.randint(1, 9)) + "期"
                    build_year = random.randint(*profile["build_year_range"])
                    total_units = random.randint(200, 3000)
                    prop_fee = round(random.uniform(1.5, 8.0), 1)

                    conn.execute("""
                        INSERT OR IGNORE INTO communities
                        (id, city, district, name, build_year, total_units, property_fee)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (community_id, city, district, name, build_year, total_units, prop_fee))

                    base_price = profile["price"]
                    # 小区间价格有波动（±20%）
                    community_price_factor = random.gauss(1.0, 0.12)
                    community_base = base_price * community_price_factor

                    # 生成挂牌数据（每个小区5-15条）
                    n_listings = random.randint(5, 15)
                    for _ in range(n_listings):
                        area = round(random.choice([60, 70, 80, 89, 90, 100, 110, 120, 140]) + random.gauss(0, 5), 1)
                        area = max(30, area)
                        unit_price = round(community_base * random.gauss(1.0, 0.08))
                        total_price = round(unit_price * area / 10000, 1)  # 万元
                        floor = random.choice(["low", "mid", "mid_high", "high"])
                        deco = random.choice(["rough", "simple", "fine", "fine", "fine"])
                        orient = random.choice(["south", "south_north", "east", "west"])
                        beds = random.choice([1, 2, 2, 3, 3, 3, 4])
                        days_ago = random.randint(1, 90)
                        listing_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

                        conn.execute("""
                            INSERT INTO listings
                            (community_id, area, total_price, unit_price, floor_level,
                             decoration, orientation, bedroom_count, listing_date, crawl_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (community_id, area, total_price, unit_price, floor,
                              deco, orient, beds, listing_date, datetime.now().strftime("%Y-%m-%d")))

                    # 生成历史成交数据（2015-2025各年各若干条）
                    for year, price_idx in HISTORICAL_PRICE_INDEX.items():
                        n_deals = random.randint(2, 8)
                        for _ in range(n_deals):
                            area = round(random.choice([60, 70, 80, 89, 90, 100, 110, 120, 140]) + random.gauss(0, 5), 1)
                            area = max(30, area)
                            hist_price = community_base * price_idx * random.gauss(1.0, 0.06)
                            unit_price = round(hist_price)
                            total_price = round(unit_price * area / 10000, 1)
                            listing_price = round(total_price * random.uniform(1.02, 1.15), 1)
                            floor = random.choice(["low", "mid", "mid_high", "high"])
                            deco = random.choice(["rough", "simple", "fine", "fine"])
                            orient = random.choice(["south", "south_north", "east", "west"])
                            beds = random.choice([1, 2, 2, 3, 3, 3, 4])
                            month = random.randint(1, 12)
                            day = random.randint(1, 28)
                            deal_date = f"{year}-{month:02d}-{day:02d}"
                            deal_cycle = random.randint(30, 180)

                            conn.execute("""
                                INSERT INTO transactions
                                (community_id, area, total_price, unit_price, listing_price,
                                 floor_level, decoration, orientation, bedroom_count,
                                 deal_date, deal_cycle)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (community_id, area, total_price, unit_price, listing_price,
                                  floor, deco, orient, beds, deal_date, deal_cycle))

                    # 生成租金数据
                    n_rentals = random.randint(3, 8)
                    for _ in range(n_rentals):
                        area = round(random.choice([40, 50, 60, 70, 80, 90, 100, 120]) + random.gauss(0, 3), 1)
                        area = max(25, area)
                        rent_psm = profile["rent"] * random.gauss(1.0, 0.15)
                        monthly_rent = round(rent_psm * area)
                        beds = random.choice([1, 1, 2, 2, 3, 3])
                        deco = random.choice(["simple", "fine", "fine"])
                        days_ago = random.randint(1, 60)
                        listing_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

                        conn.execute("""
                            INSERT INTO rentals
                            (community_id, area, monthly_rent, rent_per_sqm,
                             bedroom_count, decoration, listing_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (community_id, area, monthly_rent, round(rent_psm, 1),
                              beds, deco, listing_date))

                # 生成区域统计快照
                for year in range(2020, 2026):
                    for month in range(1, 13):
                        if year == 2025 and month > 3:
                            break
                        month_str = f"{year}-{month:02d}"
                        price_idx = HISTORICAL_PRICE_INDEX.get(year, 0.92)
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
            for year in range(2018, 2026):
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

        # 板块数据和典型案例
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

                    # 为每个板块生成2-4个典型成交案例
                    for deal_year in random.sample(
                        [y for y in [2017, 2019, 2020, 2021, 2022, 2023, 2024] if y in HISTORICAL_PRICE_INDEX],
                        min(4, len(HISTORICAL_PRICE_INDEX))
                    ):
                        price_idx = HISTORICAL_PRICE_INDEX[deal_year]
                        area = random.choice([70, 85, 89, 90, 100, 110, 120])
                        beds = 2 if area < 85 else (3 if area < 115 else 4)
                        buy_price = round(s_price * price_idx * random.gauss(1.0, 0.05))
                        total_buy = round(buy_price * area / 10000, 1)
                        current_idx = HISTORICAL_PRICE_INDEX.get(2025, 0.90)
                        current_val = round(s_price * current_idx * area / 10000, 1)
                        profit = round(current_val - total_buy, 1)
                        years = 2025 - deal_year
                        ann_ret = round(((current_val / total_buy) ** (1 / max(years, 1)) - 1) * 100, 2) if total_buy > 0 else 0
                        comm_name = random_community_name()

                        conn.execute("""
                            INSERT INTO deal_cases
                            (city, district, sector_name, community_name, deal_year,
                             area, bedroom_count, total_price_wan, unit_price,
                             current_value_wan, profit_loss_wan, annualized_return, description)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (city, district, sector, comm_name, deal_year,
                              area, beds, total_buy, buy_price,
                              current_val, profit, ann_ret,
                              f"{deal_year}年以{buy_price}元/㎡买入{area}㎡{beds}房"))

    print("示例数据生成完成！")


if __name__ == "__main__":
    generate_all()
