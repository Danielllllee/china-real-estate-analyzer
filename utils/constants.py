"""常量定义"""

# 房产类型
PROPERTY_TYPES = {
    "apartment": "普通住宅",
    "villa": "别墅",
    "commercial": "商住",
}

# 装修标准
DECORATION_LEVELS = {
    "rough": "毛坯",
    "simple": "简装",
    "fine": "精装",
    "luxury": "豪装",
}

# 装修调整系数（相对于精装基准）
DECORATION_ADJUSTMENT = {
    "rough": -0.10,
    "simple": -0.05,
    "fine": 0.0,
    "luxury": 0.08,
}

# 楼层调整系数
FLOOR_ADJUSTMENT = {
    "low": -0.03,     # 1-6层
    "mid": 0.0,       # 7-15层
    "mid_high": 0.02, # 16-25层
    "high": 0.03,     # 26层以上
    "top": -0.02,     # 顶层
    "ground": -0.05,  # 底层（1-2层）
}

# 房龄调整系数（每年折旧）
AGE_DEPRECIATION_RATE = 0.005  # 每年0.5%

# 朝向调整
ORIENTATION_ADJUSTMENT = {
    "south": 0.03,
    "south_north": 0.02,
    "east": 0.0,
    "west": -0.02,
    "north": -0.05,
}
