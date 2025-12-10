# db.py
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any
import os

<<<<<<< HEAD
DB_PATH = r"C:\Users\chand\desktop\health-ai-agent\health.db"

def get_conn():
        # DEBUGGING wrapper to show exactly which DB path the app opens and how many rows it sees
        import os, sqlite3
        print("===== DEBUG get_conn() START =====")
        print("DB_PATH (raw):", repr(DB_PATH))
        abs_path = os.path.abspath(DB_PATH)
        print("DB_PATH (abs) :", abs_path)
        print("DB file exists?:", os.path.exists(abs_path))
        try:
            conn = sqlite3.connect(abs_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # quick sanity checks
            c = conn.cursor()
            try:
                c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='goals'")
                has = bool(c.fetchone())
                print("goals table present?:", has)
                if has:
                    c.execute("SELECT COUNT(*) FROM goals")
                    cnt = c.fetchone()[0]
                    print("rows in goals:", cnt)
                    c.execute("SELECT * FROM goals LIMIT 3")
                    print("sample:", c.fetchall())
            except Exception as qerr:
                print("Query error (schema/rows):", qerr)
            print("===== DEBUG get_conn() END =====")
            return conn
        except Exception as e:
            print("ERROR connecting to DB:", e)
            raise
=======
DB_PATH = os.getenv("DB_PATH", "health.db")

def get_conn():
    # Use relative DB_PATH (or set DB_PATH env var to an absolute path)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
>>>>>>> 6d768788236e5406ac5ab5cf55c6a3d4fcc57964

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
<<<<<<< HEAD
    # inside init_db() after med_taken table creation
    c.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        medication_a TEXT,
        medication_b TEXT,
        severity TEXT,
        description TEXT,
        created_at TEXT,
        resolved INTEGER DEFAULT 0,
        note TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    # inside init_db(), add:
    c.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        goal_type TEXT NOT NULL,      -- e.g. 'steps_daily', 'weight_target'
        target_value REAL,            -- numeric target (e.g. 10000 steps, 70.0 kg)
        unit TEXT,                    -- e.g. 'steps', 'kg', 'mmHg'
        start_date TEXT,              -- ISO date string
        end_date TEXT,                -- ISO date string (optional)
        notes TEXT,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
=======
>>>>>>> 6d768788236e5406ac5ab5cf55c6a3d4fcc57964
    
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

<<<<<<< HEAD
def add_alert(user_id: int, medication_a: str, medication_b: str, severity: str, description: str, note: Optional[str] = None) -> int:
    conn = get_conn()
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute(
        "INSERT INTO alerts (user_id, medication_a, medication_b, severity, description, created_at, note) VALUES (?,?,?,?,?,?,?)",
        (user_id, medication_a or "", medication_b or "", severity or "", description or "", now, note or "")
    )
    conn.commit()
    aid = c.lastrowid
    conn.close()
    return aid

def list_alerts(user_id: int, unresolved_only: bool = True, limit: int = 100) -> List[Dict]:
    conn = get_conn()
    c = conn.cursor()
    if unresolved_only:
        rows = c.execute("SELECT id, user_id, medication_a, medication_b, severity, description, created_at, resolved, note FROM alerts WHERE user_id = ? AND resolved = 0 ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()
    else:
        rows = c.execute("SELECT id, user_id, medication_a, medication_b, severity, description, created_at, resolved, note FROM alerts WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def resolve_alert(alert_id: int) -> bool:
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE alerts SET resolved = 1 WHERE id = ?", (alert_id,))
    conn.commit()
    ok = c.rowcount > 0
    conn.close()
    return ok

# ---------- Goals ----------
# db.py
def add_goal(user_id: int, goal_title: str, goal_type: str,
             target_value=None, unit: str=None,
             start_date: str=None, end_date: str=None, notes: str=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO goals (user_id, goal_title, goal_type, target_value, unit, start_date, end_date, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, goal_title, goal_type, target_value, unit, start_date, end_date, notes))
    conn.commit()
    conn.close()
    return c.lastrowid

def list_goals(user_id: int):
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute("""
        SELECT id, user_id, goal_title, goal_type, target_value, unit, start_date, end_date, notes, created_at
        FROM goals
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_goal(goal_id: int) -> Optional[Dict]:
    conn = get_conn()
    c = conn.cursor()
    row = c.execute("SELECT id, user_id, title, goal_type, target_value, unit, start_date, end_date, notes, created_at FROM goals WHERE id = ?", (goal_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_goal(goal_id: int, **kwargs) -> bool:
    conn = get_conn()
    c = conn.cursor()

    cur = c.execute("SELECT id, goal_title, goal_type, target_value, unit, start_date, end_date, notes FROM goals WHERE id = ?", (goal_id,)).fetchone()
    if not cur:
        conn.close()
        return False

    cur = dict(cur)

    goal_title = kwargs.get("goal_title", cur["goal_title"])
    goal_type = kwargs.get("goal_type", cur["goal_type"])
    target_value = kwargs.get("target_value", cur["target_value"])
    unit = kwargs.get("unit", cur["unit"])
    start_date = kwargs.get("start_date", cur["start_date"])
    end_date = kwargs.get("end_date", cur["end_date"])
    notes = kwargs.get("notes", cur["notes"])

    # ✅ FIXED SQL QUERY GOES HERE
    c.execute("""
        UPDATE goals 
        SET goal_title=?, 
            goal_type=?, 
            target_value=?, 
            unit=?, 
            start_date=?, 
            end_date=?, 
            notes=? 
        WHERE id=?
    """, (goal_title, goal_type, target_value, unit, start_date, end_date, notes, goal_id))

    conn.commit()
    conn.close()
    return True

def delete_goal(goal_id: int) -> bool:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM goals WHERE id = ?", (goal_id,))
    if not c.fetchone():
        conn.close()
        return False
    c.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()
    return True

=======
>>>>>>> 6d768788236e5406ac5ab5cf55c6a3d4fcc57964
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