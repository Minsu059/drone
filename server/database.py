import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "drone.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drone_position (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drone_id TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            alt REAL,
            timestamp REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disaster_report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drone_id TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            alt REAL,
            timestamp REAL NOT NULL,
            person_count INTEGER DEFAULT 0,
            collapse_rate REAL DEFAULT 0.0,
            road_status TEXT DEFAULT 'normal',
            fire_detected INTEGER DEFAULT 0,
            fire_confidence REAL DEFAULT 0.0,
            disaster_type TEXT DEFAULT '',
            image_base64 TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
