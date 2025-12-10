# meds_db.py
import sqlite3
from typing import List, Dict, Optional, Tuple

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    generic TEXT,
    brand TEXT,
    form TEXT,
    strength TEXT,
    source TEXT
);

CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    med_a_id INTEGER NOT NULL,
    med_b_id INTEGER NOT NULL,
    severity TEXT,
    description TEXT,
    UNIQUE(med_a_id, med_b_id),
    FOREIGN KEY(med_a_id) REFERENCES medications(id) ON DELETE CASCADE,
    FOREIGN KEY(med_b_id) REFERENCES medications(id) ON DELETE CASCADE
);
"""

def init_meds_db(path: str):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    conn.commit()
    conn.close()

def get_conn(path: str):
    return sqlite3.connect(path)

def upsert_med(conn, name: str, generic: Optional[str]=None, brand: Optional[str]=None,
               form: Optional[str]=None, strength: Optional[str]=None, source: Optional[str]=None) -> int:
    cur = conn.cursor()
    # try find by exact name
    cur.execute("SELECT id FROM medications WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO medications (name, generic, brand, form, strength, source) VALUES (?, ?, ?, ?, ?, ?)",
        (name, generic, brand, form, strength, source)
    )
    conn.commit()
    return cur.lastrowid

# ------ robust helpers that inspect table columns at runtime ------
def _get_med_table_columns(conn: sqlite3.Connection) -> List[str]:
    """Return list of column names for medications table."""
    cur = conn.cursor()
    cols = []
    try:
        cur.execute("PRAGMA table_info(medications)")
        rows = cur.fetchall()
        cols = [r[1] for r in rows]  # 2nd column = name
    except Exception:
        cols = []
    return cols

def _row_to_dict(cols: List[str], row: tuple) -> Dict:
    """Map a fetched row tuple to dict keyed by cols (assumes SELECT matched cols order)."""
    return {cols[i]: row[i] for i in range(len(cols))}

def search_med(path: str, q: str, limit: int = 20) -> List[Dict]:
    """
    Search medications with fallback if some columns (like 'generic') don't exist.
    Returns list of dicts with only available columns.
    """
    conn = get_conn(path)
    try:
        avail_cols = _get_med_table_columns(conn)
        # ensure we always include id and name in select
        select_cols = [c for c in ["id", "name", "generic", "brand", "form", "strength", "source"] if c in avail_cols]
        if not select_cols:
            return []

        q_like = f"%{q.strip().lower()}%"

        # build WHERE clause only for existing searchable columns
        search_cols = [c for c in ["name", "generic", "brand"] if c in avail_cols]
        where_clauses = []
        params = []
        for c in search_cols:
            where_clauses.append(f"lower({c}) LIKE ?")
            params.append(q_like)
        if not where_clauses:
            # nothing to search against
            return []

        where_sql = " OR ".join(where_clauses)
        sql = f"SELECT {', '.join(select_cols)} FROM medications WHERE {where_sql} LIMIT ?"
        params.append(limit)

        cur = conn.cursor()
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        # convert row tuples to dicts keyed by select_cols
        results = []
        for r in rows:
            d = _row_to_dict(select_cols, r)
            results.append(d)
        return results
    finally:
        conn.close()

def get_med_by_id(path: str, med_id: int) -> Optional[Dict]:
    """
    Return medication dict for given id. Only returns columns that actually exist.
    """
    conn = get_conn(path)
    try:
        avail_cols = _get_med_table_columns(conn)
        select_cols = [c for c in ["id", "name", "generic", "brand", "form", "strength", "source"] if c in avail_cols]
        if not select_cols:
            return None
        sql = f"SELECT {', '.join(select_cols)} FROM medications WHERE id = ? LIMIT 1"
        cur = conn.cursor()
        cur.execute(sql, (med_id,))
        r = cur.fetchone()
        if not r:
            return None
        return _row_to_dict(select_cols, r)
    finally:
        conn.close()

def add_interaction(path: str, med_a_id: int, med_b_id: int, severity: str, description: str):
    if med_a_id == med_b_id:
        return
    conn = get_conn(path)
    cur = conn.cursor()
    # store both directions so lookups are straightforward
    try:
        cur.execute("INSERT OR IGNORE INTO interactions (med_a_id, med_b_id, severity, description) VALUES (?, ?, ?, ?)",
                    (med_a_id, med_b_id, severity, description))
        cur.execute("INSERT OR IGNORE INTO interactions (med_a_id, med_b_id, severity, description) VALUES (?, ?, ?, ?)",
                    (med_b_id, med_a_id, severity, description))
        conn.commit()
    finally:
        conn.close()

def check_interaction_by_names(path: str, name_a: str, name_b: str) -> Optional[Dict]:
    """
    Find possible interactions by searching meds by name and trying the pairs found.
    Returns dict with med_a, med_b, severity, description or None.
    """
    # candidate meds (top few)
    a = search_med(path, name_a, limit=6)
    b = search_med(path, name_b, limit=6)
    if not a or not b:
        return None

    conn = get_conn(path)
    try:
        cur = conn.cursor()
        for ma in a:
            for mb in b:
                try:
                    cur.execute("SELECT severity, description FROM interactions WHERE med_a_id = ? AND med_b_id = ? LIMIT 1", (ma["id"], mb["id"]))
                except Exception:
                    # if interactions table missing or schema mismatch, skip
                    continue
                rr = cur.fetchone()
                if rr:
                    return {"med_a": ma, "med_b": mb, "severity": rr[0], "description": rr[1]}
    finally:
        conn.close()
    return None