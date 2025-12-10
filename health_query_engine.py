# health_query_engine.py
"""
DB-only health query engine.

Usage:
    from nlp_utils import interpret_query
    from health_query_engine import answer_parsed_query

    parsed = interpret_query("How many steps did I walk last week?")
    print(answer_parsed_query(parsed, user_id=1))
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any

# re-use your db.py get_conn if available
try:
    from db import get_conn
except Exception:
    # fallback: open local health.db
    import os, sqlite3
    DBPATH = os.getenv("DB_PATH", "health.db")

    def get_conn():
        return sqlite3.connect(DBPATH, check_same_thread=False)

# ---------- helpers to probe DB schema ----------

def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (name,))
    return bool(c.fetchone())

def find_table(conn: sqlite3.Connection, candidates):
    """Return first candidate table name that exists in DB, else None."""
    for t in candidates:
        if table_exists(conn, t):
            return t
    return None

def get_columns(conn: sqlite3.Connection, table: str):
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in c.fetchall()]

def choose_col(cols, prefer):
    """Return first col in `cols` that is in prefer list."""
    for p in prefer:
        if p in cols:
            return p
    return None

# ---------- date helpers ----------

def parse_time_range(time_range: str, date_str: Optional[str]=None) -> Tuple[str, str]:
    """Return (start_iso, end_iso) inclusive date strings (YYYY-MM-DD)."""
    today = datetime.now().date()
    if time_range == "today":
        s = e = today
    elif time_range == "yesterday":
        s = e = today - timedelta(days=1)
    elif time_range == "last_7_days":
        e = today
        s = today - timedelta(days=6)
    elif time_range == "specific_date" and date_str:
        s = e = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        # latest = treat same as today for queries that need a range
        s = e = today
    return (s.isoformat(), e.isoformat())

# ---------- query implementations ----------

def get_latest_bp(conn: sqlite3.Connection, user_id: int) -> Optional[str]:
    # Try common tables that might store BP (health, health_records, vitals)
    candidates = ["health_records", "health", "vitals", "records"]
    table = find_table(conn, candidates)
    if not table:
        return None

    cols = get_columns(conn, table)

    # possible columns:
    col_user = choose_col(cols, ["user_id", "userid", "user"])
    col_type = choose_col(cols, ["type", "record_type", "name", "metric"])
    col_value = choose_col(cols, ["value", "val", "reading", "systolic", "diastolic"])
    col_date = choose_col(cols, ["date", "created_at", "timestamp", "recorded_at"])

    # find bp records where type indicates blood pressure:
    c = conn.cursor()
    type_patterns = ("bp", "blood pressure", "blood_pressure", "bloodpressure")
    where_type = ""
    params = []
    if col_type:
        where_type = " AND (" + " OR ".join([f"lower({col_type}) LIKE ?" for _ in type_patterns]) + ")"
        params.extend([f"%{p}%" for p in type_patterns])

    q = f"SELECT * FROM {table} WHERE 1=1 {('AND ' + col_user + '=?') if col_user else ''} {where_type} ORDER BY {col_date if col_date else 'rowid'} DESC LIMIT 1;"
    if col_user:
        params = [user_id] + params

    try:
        c.execute(q, params)
        row = c.fetchone()
        if not row:
            return None
        # try to present meaningful output: if systolic/diastolic columns exist use them
        if "systolic" in cols and "diastolic" in cols:
            idx_sys = cols.index("systolic")
            idx_dia = cols.index("diastolic")
            return f"{row[idx_sys]}/{row[idx_dia]} (systolic/diastolic)"
        # else if 'value' contains text like "120/80"
        if col_value and col_value in cols:
            val = row[cols.index(col_value)]
            return str(val)
        # fallback: return the whole row as string
        return str(row)
    except Exception:
        return None

def get_latest_sugar(conn: sqlite3.Connection, user_id: int) -> Optional[str]:
    # same approach as bp but search sugar/glucose
    candidates = ["health_records", "health", "vitals", "records"]
    table = find_table(conn, candidates)
    if not table:
        return None
    cols = get_columns(conn, table)
    col_user = choose_col(cols, ["user_id", "userid", "user"])
    col_type = choose_col(cols, ["type", "record_type", "name", "metric"])
    col_value = choose_col(cols, ["value", "val", "reading"])
    col_date = choose_col(cols, ["date", "created_at", "timestamp", "recorded_at"])

    c = conn.cursor()
    type_patterns = ("sugar", "glucose", "blood sugar")
    where_type = ""
    params = []
    if col_type:
        where_type = " AND (" + " OR ".join([f"lower({col_type}) LIKE ?" for _ in type_patterns]) + ")"
        params.extend([f"%{p}%" for p in type_patterns])

    q = f"SELECT * FROM {table} WHERE 1=1 {('AND ' + col_user + '=?') if col_user else ''} {where_type} ORDER BY {col_date if col_date else 'rowid'} DESC LIMIT 1;"
    if col_user:
        params = [user_id] + params

    try:
        c.execute(q, params)
        row = c.fetchone()
        if not row:
            return None
        if col_value and col_value in cols:
            return str(row[cols.index(col_value)])
        return str(row)
    except Exception:
        return None

def get_steps_sum(conn: sqlite3.Connection, user_id: int, start_iso: str, end_iso: str) -> Optional[int]:
    # Search likely tables: 'fitness', 'fitness_records', 'activity', 'steps'
    candidates = ["fitness_records", "fitness", "activity", "steps", "records"]
    table = find_table(conn, candidates)
    if not table:
        return None
    cols = get_columns(conn, table)
    col_user = choose_col(cols, ["user_id", "userid", "user"])
    col_steps = choose_col(cols, ["steps", "value", "val", "count"])
    col_date = choose_col(cols, ["date", "created_at", "timestamp", "recorded_at"])

    # we will filter rows where possibly 'type' indicates steps, but many fitness tables only contain steps
    c = conn.cursor()
    where_type = ""
    params = []

    if col_date:
        date_filter = f"{col_date} BETWEEN ? AND ?"
        params.extend([start_iso, end_iso])
    else:
        # fallback: no date column -> sum all rows (not ideal)
        date_filter = "1=1"

    if col_user:
        q = f"SELECT SUM({col_steps}) FROM {table} WHERE {col_user}=? AND {date_filter};"
        params = [user_id] + params
    else:
        q = f"SELECT SUM({col_steps}) FROM {table} WHERE {date_filter};"

    try:
        c.execute(q, params)
        s = c.fetchone()[0]
        return int(s) if s is not None else 0
    except Exception:
        return None

def get_goal_status(conn: sqlite3.Connection, user_id: int) -> Optional[str]:
    # look for goals table
    candidates = ["goals", "user_goals"]
    table = find_table(conn, candidates)
    if not table:
        return None
    cols = get_columns(conn, table)
    # find active goals for user (by latest end_date or start_date)
    col_user = choose_col(cols, ["user_id", "userid", "user"])
    col_target = choose_col(cols, ["target_value", "target", "value"])
    col_type = choose_col(cols, ["goal_type", "type", "goal"])
    col_title = choose_col(cols, ["title", "goal_title", "name"])
    col_start = choose_col(cols, ["start_date", "created_at", "start"])
    col_end = choose_col(cols, ["end_date", "end"])
    c = conn.cursor()
    params = []
    user_filter = ""
    if col_user:
        user_filter = f" WHERE {col_user}=?"
        params.append(user_id)
    q = f"SELECT * FROM {table} {user_filter} ORDER BY {col_start if col_start else 'rowid'} DESC LIMIT 5;"
    try:
        c.execute(q, params)
        rows = c.fetchall()
        if not rows:
            return "No goals found."
        out_lines = []
        for r in rows:
            title = r[cols.index(col_title)] if col_title else str(r)
            gtype = r[cols.index(col_type)] if col_type else ""
            target = r[cols.index(col_target)] if col_target else ""
            out_lines.append(f"{title} — {gtype} — Target: {target}")
        return "\n".join(out_lines)
    except Exception:
        return None

def generate_summary(conn: sqlite3.Connection, user_id: int, start_iso: str, end_iso: str) -> str:
    # quick summary: steps sum + latest bp + latest sugar
    steps = get_steps_sum(conn, user_id, start_iso, end_iso)
    bp = get_latest_bp(conn, user_id)
    sugar = get_latest_sugar(conn, user_id)
    lines = []
    lines.append(f"Summary {start_iso} -> {end_iso}:")
    lines.append(f"Steps (sum): {steps if steps is not None else 'N/A'}")
    lines.append(f"Latest BP: {bp if bp else 'N/A'}")
    lines.append(f"Latest sugar: {sugar if sugar else 'N/A'}")
    return "\n".join(lines)

# ---------- top-level dispatcher ----------

def answer_parsed_query(parsed: Dict[str, Any], user_id: int = 1) -> str:
    """
    parsed: dict produced by interpret_query()
        keys: intent, time_range, date, raw
    user_id: id integer for DB queries
    """
    conn = get_conn()
    try:
        intent = parsed.get("intent")
        time_range = parsed.get("time_range", "latest")
        date = parsed.get("date")
        start_iso, end_iso = parse_time_range(time_range, date)

        if intent == "get_bp":
            bp = get_latest_bp(conn, user_id)
            return bp or "No BP readings found."

        if intent == "get_sugar":
            sugar = get_latest_sugar(conn, user_id)
            return sugar or "No sugar readings found."

        if intent == "get_steps":
            total = get_steps_sum(conn, user_id, start_iso, end_iso)
            if total is None:
                return "No step data found."
            return f"Steps {start_iso} → {end_iso}: {total}"

        if intent == "get_goal_status":
            gs = get_goal_status(conn, user_id)
            return gs or "No goals found."

        if intent == "get_report":
            return generate_summary(conn, user_id, start_iso, end_iso)

        # unknown fallback
        return f"Sorry, I couldn't handle that query locally: {parsed.get('raw')}"
    finally:
        conn.close()

# small helper for REPL testing
if __name__ == "__main__":
    # quick smoke test
    from nlp_utils import interpret_query
    queries = [
        "What is my latest BP reading?",
        "How many steps did I walk last week?",
        "Did I reach my goal today?",
        "Show me a summary report",
        "What was my sugar on 2025-12-09?",
        "How many steps today?"
    ]
    for q in queries:
        parsed = interpret_query(q)
        print("Q:", q)
        print("Parsed:", parsed)
        resp = answer_parsed_query(parsed, user_id=1)
        print("RESP:", resp)
        print("-" * 40)