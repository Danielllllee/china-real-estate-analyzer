"""数据库操作模块"""
import sqlite3
import os
import pandas as pd
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "db.sqlite")


def get_db_path():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return DB_PATH


@contextmanager
def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """初始化数据库表结构"""
    with get_connection() as conn:
        conn.executescript("""
        -- 小区基础信息
        CREATE TABLE IF NOT EXISTS communities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            district TEXT NOT NULL,
            name TEXT NOT NULL,
            address TEXT,
            build_year INTEGER,
            total_units INTEGER,
            property_fee REAL,
            latitude REAL,
            longitude REAL,
            UNIQUE(city, district, name)
        );

        -- 挂牌数据
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            community_id INTEGER NOT NULL,
            title TEXT,
            area REAL NOT NULL,
            total_price REAL NOT NULL,
            unit_price REAL NOT NULL,
            floor_level TEXT,
            decoration TEXT,
            orientation TEXT,
            bedroom_count INTEGER,
            listing_date TEXT,
            source TEXT DEFAULT 'beike',
            crawl_date TEXT NOT NULL,
            FOREIGN KEY (community_id) REFERENCES communities(id)
        );

        -- 真实成交数据
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            community_id INTEGER NOT NULL,
            area REAL NOT NULL,
            total_price REAL NOT NULL,
            unit_price REAL NOT NULL,
            listing_price REAL,
            floor_level TEXT,
            decoration TEXT,
            orientation TEXT,
            bedroom_count INTEGER,
            deal_date TEXT NOT NULL,
            deal_cycle INTEGER,
            source TEXT DEFAULT 'beike',
            FOREIGN KEY (community_id) REFERENCES communities(id)
        );

        -- 租金数据
        CREATE TABLE IF NOT EXISTS rentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            community_id INTEGER NOT NULL,
            area REAL NOT NULL,
            monthly_rent REAL NOT NULL,
            rent_per_sqm REAL NOT NULL,
            bedroom_count INTEGER,
            decoration TEXT,
            listing_date TEXT,
            source TEXT DEFAULT 'beike',
            FOREIGN KEY (community_id) REFERENCES communities(id)
        );

        -- 区域统计快照（按月）
        CREATE TABLE IF NOT EXISTS district_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            district TEXT NOT NULL,
            month TEXT NOT NULL,
            avg_unit_price REAL,
            median_unit_price REAL,
            transaction_count INTEGER,
            avg_rent_per_sqm REAL,
            rent_to_price_ratio REAL,
            listing_count INTEGER,
            avg_deal_cycle INTEGER,
            UNIQUE(city, district, month)
        );

        -- 土地出让数据
        CREATE TABLE IF NOT EXISTS land_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            district TEXT NOT NULL,
            land_area REAL,
            floor_area_ratio REAL,
            floor_price REAL NOT NULL,
            total_price REAL,
            sale_date TEXT NOT NULL,
            buyer TEXT
        );

        -- 板块数据
        CREATE TABLE IF NOT EXISTS sectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            district TEXT NOT NULL,
            sector_name TEXT NOT NULL,
            avg_unit_price REAL,
            avg_rent_per_sqm REAL,
            community_count INTEGER,
            description TEXT,
            UNIQUE(city, district, sector_name)
        );

        -- 典型成交案例
        CREATE TABLE IF NOT EXISTS deal_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            district TEXT NOT NULL,
            sector_name TEXT,
            community_name TEXT NOT NULL,
            deal_year INTEGER NOT NULL,
            area REAL NOT NULL,
            bedroom_count INTEGER,
            total_price_wan REAL NOT NULL,
            unit_price REAL NOT NULL,
            current_value_wan REAL,
            profit_loss_wan REAL,
            annualized_return REAL,
            description TEXT
        );

        -- 宏观经济数据
        CREATE TABLE IF NOT EXISTS macro_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            year INTEGER NOT NULL,
            population REAL,
            gdp REAL,
            gdp_growth REAL,
            disposable_income REAL,
            income_growth REAL,
            cpi REAL,
            UNIQUE(city, year)
        );
        """)


def query_df(sql, params=None):
    """执行查询并返回DataFrame"""
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params or [])


def execute(sql, params=None):
    """执行写操作"""
    with get_connection() as conn:
        conn.execute(sql, params or [])


def executemany(sql, params_list):
    """批量执行写操作"""
    with get_connection() as conn:
        conn.executemany(sql, params_list)
