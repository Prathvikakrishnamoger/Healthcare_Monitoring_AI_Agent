# tests/test_meds_db.py
import os
from meds_db import init_meds_db, get_conn, upsert_med, search_med, add_interaction, check_interaction_by_names

TEST_DB = "test_meds.db"

def setup_module(module):
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    init_meds_db(TEST_DB)

def teardown_module(module):
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_upsert_and_search():
    conn = get_conn(TEST_DB)
    mid = upsert_med(conn, "XMed", generic="x", brand="xb", form="tab", strength="100mg", source="unit")
    assert mid is not None
    res = search_med(TEST_DB, "xmed")
    assert any(r["name"].lower() == "xmed" for r in res)
    conn.close()

def test_interaction_lookup():
    conn = get_conn(TEST_DB)
    ida = upsert_med(conn, "A", generic="a")
    idb = upsert_med(conn, "B", generic="b")
    add_interaction(TEST_DB, ida, idb, "danger", "testdesc")
    res = check_interaction_by_names(TEST_DB, "A", "B")
    assert res and res["severity"] == "danger"