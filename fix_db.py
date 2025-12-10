import sqlite3
import os

db_path = r"C:\Users\chand\desktop\health-ai-agent\health.db"  # <-- change only if your DB filename is different

if not os.path.exists(db_path):
    raise FileNotFoundError(f"Cannot find database at: {db_path}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

print("Before:")
c.execute("PRAGMA table_info(goals)")
print(c.fetchall())

try:
    c.execute("ALTER TABLE goals ADD COLUMN goal_title TEXT")
    print("Added column goal_title.")
except Exception as e:
    print("Column already exists or cannot be added:", e)

conn.commit()

print("After:")
c.execute("PRAGMA table_info(goals)")
print(c.fetchall())

conn.close()
print("Done.")