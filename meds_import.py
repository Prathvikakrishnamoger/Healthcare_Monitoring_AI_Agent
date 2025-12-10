# meds_import.py
import csv
import sys
from meds_db import get_conn, upsert_med, add_interaction

DB_PATH = "meds_india.db"

def import_meds(meds_csv):
    conn = get_conn(DB_PATH)
    with open(meds_csv, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            name = row.get('name') or row.get('Name') or ''
            if not name: 
                continue
            upsert_med(conn,
                       name=name.strip(),
                       generic=(row.get('generic') or row.get('Generic') or '').strip() or None,
                       brand=(row.get('brand') or '').strip() or None,
                       form=(row.get('form') or '').strip() or None,
                       strength=(row.get('strength') or '').strip() or None,
                       source=(row.get('source') or '').strip() or None)
    conn.close()

def import_interactions(interactions_csv):
    # interactions.csv should contain med names; we find ids by name search
    from meds_db import search_med, get_med_by_id
    conn = get_conn(DB_PATH)
    with open(interactions_csv, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            a = (row.get('name_a') or '').strip()
            b = (row.get('name_b') or '').strip()
            if not a or not b:
                continue
            # find IDs by exact search
            a_candidates = search_med(DB_PATH, a, limit=5)
            b_candidates = search_med(DB_PATH, b, limit=5)
            if not a_candidates or not b_candidates:
                print("WARN: missing med in DB:", a, b)
                continue
            aid = a_candidates[0]['id']
            bid = b_candidates[0]['id']
            sev = (row.get('severity') or 'warn').strip()
            desc = (row.get('description') or '').strip()
            add_interaction(DB_PATH, aid, bid, sev, desc)
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python meds_import.py meds.csv interactions.csv")
        sys.exit(1)
    import_meds(sys.argv[1])
    import_interactions(sys.argv[2])
    print("Import finished")