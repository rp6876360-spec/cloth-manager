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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_cloth(image_path, season, category, keywords):
    """添加衣服记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO clothes (image_path, season, category, keywords) VALUES (?, ?, ?, ?)",
        (image_path, season, category, keywords)
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
