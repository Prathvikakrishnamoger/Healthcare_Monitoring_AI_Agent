# check_goals.py
import sqlite3, glob, os
ROOT = r"C:\Users\chand\desktop\health-ai-agent"
os.chdir(ROOT)

db_files = glob.glob(os.path.join(ROOT, "*.db"))
if not db_files:
    print("No .db files found.")
    raise SystemExit

for db in db_files:
    print("\n---", db, "---")
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='goals'")
        if not c.fetchone():
            print("  no 'goals' table")
            conn.close()
            continue

        c.execute("SELECT COUNT(*) FROM goals")
        cnt = c.fetchone()[0]
        print("  rows in goals:", cnt)

        if cnt:
            c.execute("SELECT * FROM goals LIMIT 5")
            rows = c.fetchall()
            print("  sample rows (up to 5):")
            for r in rows:
                print("   ", r)
        conn.close()
    except Exception as e:
        print("  error reading DB:", e)