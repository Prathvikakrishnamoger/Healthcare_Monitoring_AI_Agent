import sqlite3, os, glob, shutil

ROOT = r"C:\Users\chand\desktop\health-ai-agent"
os.chdir(ROOT)

# find DB files (will run migration on any DB that contains a 'goals' table)
db_files = glob.glob(os.path.join(ROOT, "*.db"))
if not db_files:
    raise SystemExit("No .db files found in project folder.")

for db_path in db_files:
    print("Processing:", db_path)
    # backup first
    bak = db_path + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(db_path, bak)
        print("  - backup created:", bak)
    else:
        print("  - backup already exists:", bak)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # ensure goals table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='goals'")
    if not c.fetchone():
        print("  - no 'goals' table, skipping.")
        conn.close()
        continue

    # show current columns
    c.execute("PRAGMA table_info(goals)")
    cols = c.fetchall()
    col_names = [r[1] for r in cols]
    print("  - current columns:", col_names)

    # create new table with correct schema
    # adjust types to match your app's expectations
    create_sql = """
    CREATE TABLE IF NOT EXISTS goals_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        goal_title TEXT,
        goal_type TEXT,
        target_value REAL,
        unit TEXT,
        start_date TEXT,
        end_date TEXT,
        notes TEXT,
        created_at TEXT
    );
    """
    try:
        c.execute("BEGIN")
        c.execute(create_sql)
        print("  - created goals_new table.")
    except Exception as e:
        print("  - failed to create goals_new:", e)
        c.execute("ROLLBACK")
        conn.close()
        continue

    # copy data: if old table has 'title', map it to goal_title; otherwise try existing 'goal_title'
    # build select clause depending on available columns
    select_cols = []
    for needed in ("id", "user_id"):
        if needed in col_names:
            select_cols.append(needed)
        else:
            select_cols.append("NULL AS " + needed)

    # goal_title: prefer existing goal_title, else fallback to title, else NULL
    if "goal_title" in col_names and "title" in col_names:
        title_expr = "COALESCE(goal_title, title) AS goal_title"
    elif "goal_title" in col_names:
        title_expr = "goal_title AS goal_title"
    elif "title" in col_names:
        title_expr = "title AS goal_title"
    else:
        title_expr = "NULL AS goal_title"
    select_cols.append(title_expr)

    # remaining columns, use column or NULL if missing
    for name in ("goal_type", "target_value", "unit", "start_date", "end_date", "notes", "created_at"):
        if name in col_names:
            select_cols.append(name)
        else:
            select_cols.append("NULL AS " + name)

    select_sql = "SELECT " + ", ".join(select_cols) + " FROM goals"
    insert_sql = "INSERT INTO goals_new (id, user_id, goal_title, goal_type, target_value, unit, start_date, end_date, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

    try:
        c.execute(select_sql)
        rows = c.fetchall()
        print(f"  - copying {len(rows)} rows into goals_new...")
        if rows:
            c.executemany(insert_sql, rows)
        # drop old table and rename
        c.execute("DROP TABLE goals")
        c.execute("ALTER TABLE goals_new RENAME TO goals")
        conn.commit()
        print("  - migration complete for", db_path)
    except Exception as e:
        conn.rollback()
        print("  - migration failed:", e)
        print("  - restore from backup if necessary:", bak)
    finally:
        conn.close()

print("All DB files processed.")