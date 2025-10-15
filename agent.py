# app.py
import streamlit as st
from db import init_db, add_medication, list_medications

init_db()

st.set_page_config(page_title="Health AI Agent — MVP", layout="centered")
st.title("Healthcare Monitoring — Week 1 MVP")

st.markdown("Add a medication (this stores to a local SQLite DB).")

with st.form("add_med"):
    name = st.text_input("Medication name")
    dose = st.text_input("Dose (e.g., 10 mg)")
    times = st.text_input("Times (comma separated HH:MM)", value="08:00,20:00")
    submitted = st.form_submit_button("Add medication")
    if submitted:
        if not name.strip():
            st.error("Medication name is required.")
        else:
            add_medication(name.strip(), dose.strip(), times.strip())
            st.success(f"Added: {name.strip()}")

st.divider()
st.subheader("Stored medications")
meds = list_medications()
if not meds:
    st.info("No medications yet. Add one above.")
else:
    for m in meds:
        st.write(f"- **{m['name']}** — {m['dose']} — Times: {m['times']} (added {m['created_at']})")
