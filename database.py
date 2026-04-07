import sqlite3
import os
from datetime import datetime

DB_PATH = "clothes.db"

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clothes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT NOT NULL,
            season TEXT NOT NULL,
            category TEXT NOT NULL,
            keywords TEXT,
            brand TEXT,
            price REAL,
            style TEXT,
            color TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS outfits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            items TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_cloth(image_path, season, category, keywords, brand=None, price=None, style=None, color=None):
    """添加衣服记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO clothes (image_path, season, category, keywords, brand, price, style, color) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (image_path, season, category, keywords, brand, price, style, color)
    )
    conn.commit()
    conn.close()

def get_all_clothes():
    """获取所有衣服"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clothes ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_clothes_by_filter(season=None, category=None, keyword=None):
    """根据条件筛选衣服"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT * FROM clothes WHERE 1=1"
    params = []

    if season and season != "全部":
        query += " AND season = ?"
        params.append(season)

    if category and category != "全部":
        query += " AND category = ?"
        params.append(category)

    if keyword:
        query += " AND keywords LIKE ?"
        params.append(f"%{keyword}%")

    query += " ORDER BY created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_cloth(cloth_id):
    """删除衣服记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clothes WHERE id = ?", (cloth_id,))
    conn.commit()
    conn.close()

def get_clothes_by_category(category):
    """按类型获取衣服（用于搭配）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clothes WHERE category = ? ORDER BY created_at DESC", (category,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def save_outfit(name, items_json):
    """保存搭配"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO outfits (name, items) VALUES (?, ?)",
        (name, items_json)
    )
    conn.commit()
    conn.close()

def get_all_outfits():
    """获取所有搭配"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM outfits ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_outfit(outfit_id):
    """删除搭配"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM outfits WHERE id = ?", (outfit_id,))
    conn.commit()
    conn.close()

def get_statistics():
    """获取统计数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 各类型数量
    cursor.execute("SELECT category, COUNT(*) FROM clothes GROUP BY category")
    category_stats = dict(cursor.fetchall())

    # 各颜色数量
    cursor.execute("SELECT color, COUNT(*) FROM clothes WHERE color IS NOT NULL AND color != '' GROUP BY color")
    color_stats = dict(cursor.fetchall())

    # 各风格数量
    cursor.execute("SELECT style, COUNT(*) FROM clothes WHERE style IS NOT NULL AND style != '' GROUP BY style")
    style_stats = dict(cursor.fetchall())

    # 各季节数量
    cursor.execute("SELECT season, COUNT(*) FROM clothes GROUP BY season")
    season_stats = dict(cursor.fetchall())

    # 总数量和总价
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(price), 0) FROM clothes")
    total_count, total_price = cursor.fetchone()

    conn.close()

    return {
        'category': category_stats,
        'color': color_stats,
        'style': style_stats,
        'season': season_stats,
        'total_count': total_count,
        'total_price': total_price or 0
    }
