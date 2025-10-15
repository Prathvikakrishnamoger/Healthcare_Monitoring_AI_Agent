# db.py
import sqlite3
from datetime import datetime
from typing import List, Tuple

DB_PATH = "health.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS medications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        dose TEXT,
        times TEXT,         -- comma separated HH:MM
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()

def add_medication(name: str, dose: str, times: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO medications (name,dose,times,created_at) VALUES (?,?,?,?)",
              (name, dose, times, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def list_medications() -> List[Tuple]:
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute("SELECT id, name, dose, times, created_at FROM medications ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

if __name__ == "__main__":
    init_db()
    print("DB initialized.")
