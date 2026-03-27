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
        -- 区域统计（经过核实的真实数据）
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

        -- 城市宏观经济数据（来自统计局公报）
        CREATE TABLE IF NOT EXISTS macro_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            data_year TEXT NOT NULL,
            gdp REAL,
            population REAL,
            per_capita_income REAL,
            UNIQUE(city, data_year)
        );
        """)


def ensure_data():
    """确保数据库已初始化且有最新真实数据"""
    db_path = get_db_path()
    need_rebuild = False
    if not os.path.exists(db_path):
        need_rebuild = True
    else:
        try:
            with get_connection() as conn:
                tables = [r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()]
                # 检查是否有旧表（虚假数据残留）
                fake_tables = {'communities', 'listings', 'transactions',
                               'rentals', 'deal_cases', 'land_sales',
                               'sectors'}
                if fake_tables & set(tables):
                    need_rebuild = True
                # 检查 macro_data 表是否存在（新增）
                if 'macro_data' not in tables:
                    need_rebuild = True
                # 检查 district_stats 是否有租金数据
                if not need_rebuild:
                    rent_count = conn.execute(
                        "SELECT COUNT(*) FROM district_stats WHERE avg_rent_per_sqm IS NOT NULL"
                    ).fetchone()[0]
                    if rent_count == 0:
                        need_rebuild = True
                # 检查是否有数据
                if not need_rebuild:
                    ds_count = conn.execute(
                        "SELECT COUNT(*) FROM district_stats"
                    ).fetchone()[0]
                    if ds_count == 0:
                        need_rebuild = True
        except Exception:
            need_rebuild = True

    if need_rebuild:
        if os.path.exists(db_path):
            os.remove(db_path)
        init_db()
        from data.sample.generate_sample import generate_all
        generate_all()


# 模块加载时自动确保数据库就绪
ensure_data()


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
