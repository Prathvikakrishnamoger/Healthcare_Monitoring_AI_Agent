# seed_meds_india.py
import csv
from meds_db import init_meds_db, get_conn, upsert_med, add_interaction

DB_PATH = "meds_india.db"
CSV_PATH = "meds_india_sample.csv"

def seed():
    init_meds_db(DB_PATH)
    conn = get_conn(DB_PATH)
    reader = csv.DictReader(open(CSV_PATH, encoding="utf8"))
    mapping = {}  # name -> id
    for r in reader:
        name = r.get("name") or r.get("Name")
        generic = r.get("generic")
        brand = r.get("brand")
        form = r.get("form")
        strength = r.get("strength")
        source = r.get("source")
        if not name:
            continue
        mid = upsert_med(conn, name=name.strip(), generic=generic, brand=brand, form=form, strength=strength, source=source)
        mapping[name.strip().lower()] = mid
    # Re-read CSV to add interactions
    conn.close()
    conn = get_conn(DB_PATH)
    for r in csv.DictReader(open(CSV_PATH, encoding="utf8")):
        name = (r.get("name") or "").strip()
        interacts = (r.get("interacts_with") or "").strip()
        severity = (r.get("severity") or "").strip()
        desc = (r.get("interaction_text") or "").strip()
        if name and interacts:
            a = mapping.get(name.lower())
            b = mapping.get(interacts.lower())
            if a and b:
                add_interaction(DB_PATH, a, b, severity or "unknown", desc or f"Interaction: {name} <-> {interacts}")
    conn.close()

if __name__ == "__main__":
    seed()
    print("seeded", DB_PATH)