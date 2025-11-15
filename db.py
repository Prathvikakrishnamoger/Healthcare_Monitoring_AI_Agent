# db.py
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any
import os

DB_PATH = os.getenv("DB_PATH", "health.db")

def get_conn():
    # Use relative DB_PATH (or set DB_PATH env var to an absolute path)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables if they don't exist."""
    conn = get_conn()
    c = conn.cursor()
    # users table (simple)
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        dob TEXT,
        phone TEXT,
        created_at TEXT
    )
    """)

    # medications table (includes user_id)
    c.execute("""
    CREATE TABLE IF NOT EXISTS medications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        dose TEXT,
        times TEXT,
        frequency TEXT,
        notes TEXT,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    # health records
    c.execute("""
    CREATE TABLE IF NOT EXISTS health_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT,
        value TEXT,
        notes TEXT,
        recorded_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    # fitness records
    c.execute("""
    CREATE TABLE IF NOT EXISTS fitness_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        steps INTEGER,
        calories INTEGER,
        record_date TEXT,
        notes TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    # --- inside init_db(), add this table creation (run once via init_db) ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS med_taken (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    medication_id INTEGER NOT NULL,
    taken_at TEXT,
    note TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(medication_id) REFERENCES medications(id)
    )
    """)
    
    conn.commit()
    conn.close()

# ---------- Users ----------
def add_user(name: str, dob: Optional[str] = None, phone: Optional[str] = None) -> int:
    conn = get_conn()
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute("INSERT INTO users (name, dob, phone, created_at) VALUES (?,?,?,?)", (name, dob or "", phone or "", now))
    conn.commit()
    uid = c.lastrowid
    conn.close()
    return uid

def list_users() -> List[Dict]:
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute("SELECT id, name, dob, phone, created_at FROM users ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ---------- Medications ----------
def add_medication(name: str, dose: str, times: str, user_id: int = 1, frequency: str = "Daily", notes: Optional[str] = None) -> int:
    conn = get_conn()
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute(
        "INSERT INTO medications (user_id, name, dose, times, frequency, notes, created_at) VALUES (?,?,?,?,?,?,?)",
        (user_id, name, dose, times, frequency, notes or "", now)
    )
    conn.commit()
    last_id = c.lastrowid
    conn.close()
    return last_id

def list_medications(user_id: Optional[int] = None) -> List[Dict]:
    conn = get_conn()
    c = conn.cursor()
    if user_id is not None:
        rows = c.execute("SELECT id, user_id, name, dose, times, frequency, notes, created_at FROM medications WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    else:
        rows = c.execute("SELECT id, user_id, name, dose, times, frequency, notes, created_at FROM medications ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_medication(med_id: int) -> bool:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM medications WHERE id = ?", (med_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False
    c.execute("DELETE FROM medications WHERE id = ?", (med_id,))
    conn.commit()
    conn.close()
    return True

# ---------- Health records ----------
def add_health_record(user_id: int, type_: str, value: str, notes: Optional[str] = None) -> int:
    conn = get_conn()
    c = conn.cursor()
    recorded_at = datetime.utcnow().isoformat()
    c.execute("INSERT INTO health_records (user_id, type, value, notes, recorded_at) VALUES (?,?,?,?,?)",
              (user_id, type_, value, notes or "", recorded_at))
    conn.commit()
    rid = c.lastrowid
    conn.close()
    return rid

def list_health_records(user_id: int, record_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
    conn = get_conn()
    c = conn.cursor()
    if record_type:
        rows = c.execute("SELECT id, user_id, type, value, notes, recorded_at FROM health_records WHERE user_id = ? AND type = ? ORDER BY recorded_at DESC LIMIT ?", (user_id, record_type, limit)).fetchall()
    else:
        rows = c.execute("SELECT id, user_id, type, value, notes, recorded_at FROM health_records WHERE user_id = ? ORDER BY recorded_at DESC LIMIT ?", (user_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ---------- Fitness records ----------
def add_fitness_record(user_id: int, steps: Optional[int] = None, calories: Optional[int] = None, record_date: Optional[str] = None, notes: Optional[str] = None) -> int:
    conn = get_conn()
    c = conn.cursor()
    if record_date is None:
        record_date = datetime.utcnow().isoformat()
    c.execute("INSERT INTO fitness_records (user_id, steps, calories, record_date, notes) VALUES (?,?,?,?,?)",
              (user_id, steps, calories, record_date, notes or ""))
    conn.commit()
    fid = c.lastrowid
    conn.close()
    return fid

def list_fitness_records(user_id: int, limit: int = 100) -> List[Dict]:
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute("SELECT id, user_id, steps, calories, record_date, notes FROM fitness_records WHERE user_id = ? ORDER BY record_date DESC LIMIT ?", (user_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ---------- Helpers ----------
def get_user(user_id: int) -> Optional[Dict]:
    conn = get_conn()
    c = conn.cursor()
    row = c.execute("SELECT id, name, dob, phone, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

# ---------- Medication taken (events) ----------
def add_med_taken(user_id: int, medication_id: int, taken_at: Optional[str] = None, note: Optional[str] = None) -> int:
    """
    Record a medication as taken. taken_at should be ISO string, defaults to UTC now.
    Returns inserted id.
    """
    conn = get_conn()
    c = conn.cursor()
    t = taken_at or datetime.utcnow().isoformat()
    c.execute(
        "INSERT INTO med_taken (user_id, medication_id, taken_at, note) VALUES (?,?,?,?)",
        (user_id, medication_id, t, note or "")
    )
    conn.commit()
    last = c.lastrowid
    conn.close()
    return last

def list_med_taken(user_id: int, medication_id: Optional[int] = None, limit: int = 100) -> List[Dict]:
    conn = get_conn()
    c = conn.cursor()
    if medication_id:
        rows = c.execute(
            "SELECT id, user_id, medication_id, taken_at, note FROM med_taken WHERE user_id = ? AND medication_id = ? ORDER BY taken_at DESC LIMIT ?",
            (user_id, medication_id, limit)
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT id, user_id, medication_id, taken_at, note FROM med_taken WHERE user_id = ? ORDER BY taken_at DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_medication(med_id: int) -> Optional[Dict]:
    conn = get_conn()
    c = conn.cursor()
    row = c.execute("SELECT id, user_id, name, dose, times, frequency, notes, created_at FROM medications WHERE id = ?", (med_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_medication(med_id: int, name: Optional[str]=None, dose: Optional[str]=None, times: Optional[str]=None, frequency: Optional[str]=None, notes: Optional[str]=None) -> bool:
    # simple partial update
    conn = get_conn()
    c = conn.cursor()
    # fetch current
    cur = c.execute("SELECT name,dose,times,frequency,notes FROM medications WHERE id = ?", (med_id,)).fetchone()
    if not cur:
        conn.close()
        return False
    cur = dict(cur)
    name = name if name is not None else cur["name"]
    dose = dose if dose is not None else cur["dose"]
    times = times if times is not None else cur["times"]
    frequency = frequency if frequency is not None else cur["frequency"]
    notes = notes if notes is not None else cur["notes"]
    c.execute("UPDATE medications SET name=?, dose=?, times=?, frequency=?, notes=? WHERE id=?",
              (name, dose, times, frequency, notes, med_id))
    conn.commit()
    conn.close()
    return True

# Quick init when run directly
if __name__ == "__main__":
    init_db()
    print("Tables re-initialized successfully.")