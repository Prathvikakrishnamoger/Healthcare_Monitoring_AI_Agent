import sqlite3, os, pprint

db = r"C:\Users\chand\desktop\health-ai-agent\health.db"
print("exists:", os.path.exists(db))

conn = sqlite3.connect(db)
c = conn.cursor()

c.execute("PRAGMA table_info(goals)")
print("schema:", c.fetchall())

c.execute("SELECT COUNT(*) FROM goals")
print("rows:", c.fetchone()[0])

c.execute("""
SELECT id, user_id, goal_title, goal_type, target_value, start_date 
FROM goals 
ORDER BY created_at DESC 
LIMIT 5
""")
print("sample rows:")
for r in c.fetchall():
    pprint.pprint(r)

conn.close()