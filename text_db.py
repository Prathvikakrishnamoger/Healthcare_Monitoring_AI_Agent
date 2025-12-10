# test_db.py
import db
from pprint import pprint

print("Initializing DB (creates tables if missing)...")
db.init_db()

print("Creating test user...")
uid = db.add_user("Day3 Test", "1990-01-01", "9999999999")
print("user id:", uid)

print("Adding medication for user...")
mid = db.add_medication("TestMed", "10 mg", "08:00,20:00", user_id=uid)
print("med id:", mid)

print("Medications for user:")
pprint(db.list_medications(uid))

print("Adding a health record...")
hid = db.add_health_record(uid, "bp", "120/80", "repl test")
print("health records:")
pprint(db.list_health_records(uid))

print("Adding a fitness record...")
fid = db.add_fitness_record(uid, steps=1234, calories=40)
print("fitness records:")
pprint(db.list_fitness_records(uid))

print("Get medication by id (helper):")
try:
    pprint(db.get_medication(mid))
except Exception as e:
    print("get_medication missing or failed:", e)

print("Deleting med and listing again...")
db.delete_medication(mid)
pprint(db.list_medications(uid))
print("DONE")
