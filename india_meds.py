import sqlite3
import os

DB_PATH = "meds_india.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create medications table if not exists."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT,
            salt TEXT,
            dose_form TEXT,
            strength TEXT,
            indication TEXT,
            manufacturer TEXT,
            price REAL,
            source_url TEXT
        );
    """)
    conn.commit()
    conn.close()

def add_med(m):
    """Insert a medication dictionary into DB."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO medications (name, brand, salt, dose_form, strength, indication, manufacturer, price, source_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        m.get("name"),
        m.get("brand"),
        m.get("salt"),
        m.get("dose_form"),
        m.get("strength"),
        m.get("indication"),
        m.get("manufacturer"),
        m.get("price"),
        m.get("source_url"),
    ))
    conn.commit()
    rid = c.lastrowid
    conn.close()
    return rid

def search_meds(query, limit=20):
    """Search for medications by name, brand, or salt."""
    conn = get_conn()
    c = conn.cursor()
    q = f"%{query.lower()}%"
    c.execute("""
        SELECT * FROM medications
        WHERE lower(name) LIKE ? OR lower(brand) LIKE ? OR lower(salt) LIKE ?
        LIMIT ?
    """, (q, q, q, limit))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_med_by_id(mid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM medications WHERE id = ?", (mid,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------- SAMPLE DATA INSERT (RUN THIS ONCE) ----------------
if __name__ == "__main__":
    init_db()

    sample_meds = [
        {
            "name": "Paracetamol",
            "brand": "Dolo 650",
            "salt": "Paracetamol",
            "dose_form": "Tablet",
            "strength": "650mg",
            "indication": "Fever, pain relief",
            "manufacturer": "Micro Labs Ltd",
            "price": 30.0,
            "source_url": "https://www.1mg.com"
        },
        {
            "name": "Ciprofloxacin",
            "brand": "Ciplox",
            "salt": "Ciprofloxacin",
            "dose_form": "Tablet",
            "strength": "500mg",
            "indication": "Bacterial infections",
            "manufacturer": "Cipla Ltd",
            "price": 50.0,
            "source_url": "https://www.1mg.com"
        }
    ]

    for m in sample_meds:
        add_med(m)

    print("Sample medications inserted into meds_india.db")