# app.py 

import streamlit as st
<<<<<<< HEAD
from nlp_utils import interpret_query
from health_query_engine import answer_parsed_query
=======
>>>>>>> 6d768788236e5406ac5ab5cf55c6a3d4fcc57964
import re
import os
import math
import pandas as pd
<<<<<<< HEAD
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import drug_interactions as di
import json
from typing import Optional, List, Dict, Any

from datetime import datetime, date, time, timezone, timedelta
from india_meds import init_db, search_meds, get_med_by_id
init_db()
from india_meds import  init_db as init_india_db
import interactions
# ensure India meds DB exists
try:
    init_india_db()
except Exception:
    pass
=======

from datetime import datetime, date, time, timezone, timedelta
>>>>>>> 6d768788236e5406ac5ab5cf55c6a3d4fcc57964

# ---------------- Time Formatting Helper ----------------
IST = timezone(timedelta(hours=5, minutes=30))

def fmt_dt_for_display(dt_obj):
    """Convert datetime/ISO-string to IST and return formatted string."""
    if not dt_obj:
        return "—"
    try:
        if isinstance(dt_obj, str):
            # fromisoformat handles many ISO-like strings
            dt_obj = datetime.fromisoformat(dt_obj)
        if getattr(dt_obj, "tzinfo", None) is None or dt_obj.tzinfo.utcoffset(dt_obj) is None:
            dt_obj = dt_obj.replace(tzinfo=timezone.utc)
        local_dt = dt_obj.astimezone(IST)
        return local_dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(dt_obj)

# --------- Helpers: validation & time parsing ---------
def validate_time_str(tstr):
    """Return True if 'HH:MM' 24h format."""
    return bool(re.match(r'^[0-2]?\d:[0-5]\d$', tstr))

def validate_dose(dose):
    """Basic dose validation: not empty and reasonable length."""
    if not dose:
        return True   # dose optional
    return 1 <= len(dose) <= 60

def minutes_until(time_hhmm: str):
    """Return minutes from now (IST) until the given HH:MM. Returns None on parse failure."""
    try:
        # use UTC -> convert to IST for comparison
        now_utc = datetime.now(timezone.utc)
        now_ist = now_utc.astimezone(IST)
        t = datetime.strptime(time_hhmm, "%H:%M").time()
    except Exception:
        return None
    med_dt = datetime.combine(now_ist.date(), t)
    if med_dt.tzinfo is None:
        med_dt = med_dt.replace(tzinfo=IST)
    diff_seconds = (med_dt - now_ist).total_seconds()
    return int(diff_seconds // 60)

# ---------------- DB / agent imports ----------------
# Attempt to import an agent wrapper first (preferred)
try:
    from agent import HealthAgent
    agent_available = True
except Exception:
    HealthAgent = None
    agent_available = False

# Try to import SQLAlchemy models (optional)
try:
    from models import init_db as models_init_db, get_engine_and_session, User, Medication, HealthRecord, FitnessRecord
    sqlalchemy_available = True
except Exception:
    models_init_db = None
    get_engine_and_session = None
    User = Medication = HealthRecord = FitnessRecord = None
    sqlalchemy_available = False

# Try db.py (sqlite helper) fallback
try:
    import db as db_module
    db_available = True
except Exception:
    db_module = None
    db_available = False

# ---------------- Init DB / Agent ----------------
# If SQLAlchemy models available, ensure tables exist
if models_init_db:
    try:
        models_init_db()
    except Exception:
        pass

# Initialize agent in session_state (if available)
if HealthAgent:
    if "agent" not in st.session_state:
        try:
            st.session_state.agent = HealthAgent()
        except Exception:
            st.session_state.agent = None
    agent = st.session_state.agent
else:
    agent = None

# Prepare SQLAlchemy session fallback if available
SessionLocal = None
session = None
if get_engine_and_session:
    try:
        engine, SessionLocal = get_engine_and_session()
        session = SessionLocal()
    except Exception:
        session = None

# Optional seeding helper (won't crash if missing)
try:
    from seed_data import seed_default_data
except Exception:
    seed_default_data = None

# If db_module and seed function exist, ensure at least one user (best-effort)
if db_module and seed_default_data:
    try:
        if db_module.list_users() == []:
            seed_default_data()
    except Exception:
        pass

# ---------------- Streamlit page setup ----------------
st.set_page_config(page_title="Healthcare Monitoring AI Agent", layout="centered")
st.title("💊 Healthcare Monitoring AI Agent")

# ---------------- Sidebar: users ----------------
st.sidebar.header("Select or Add User")

# Gather user list from whichever backend is available
users_named = []
try:
    if agent and hasattr(agent, "list_users"):
        users_list = agent.list_users() or []
        users_named = [(u.get("id"), u.get("name")) for u in users_list]
    elif db_module and hasattr(db_module, "list_users"):
        users_list = db_module.list_users() or []
        users_named = [(u.get("id"), u.get("name")) for u in users_list]
    elif session and User is not None:
        rows = session.query(User).order_by(User.id).all()
        users_named = [(u.id, u.name) for u in rows]
    else:
        users_named = []
except Exception:
    users_named = []

names_for_select = [n for (_id, n) in users_named] if users_named else ["No users found"]
user_choice = st.sidebar.selectbox("Select User", names_for_select)

with st.sidebar.expander("➕ Add New User"):
    with st.form("add_user_form_v1"):
        name = st.text_input("Full Name")
        dob = st.text_input("DOB (YYYY-MM-DD)")
        phone = st.text_input("Phone")
        add_user_btn = st.form_submit_button("Add User")
        if add_user_btn:
            if not name.strip():
                st.error("Please enter a name.")
            else:
                try:
                    if agent and hasattr(agent, "add_user"):
                        new_id = agent.add_user(name.strip(), dob.strip() or None, phone.strip() or None)
                    elif db_module and hasattr(db_module, "add_user"):
                        new_id = db_module.add_user(name.strip(), dob.strip() or None, phone.strip() or None)
                    elif session and User is not None:
                        u = User(name=name.strip(), dob=dob.strip(), phone=phone.strip())
                        session.add(u)
                        session.commit()
                        new_id = u.id
                    else:
                        new_id = None
                    st.success("✅ User added successfully.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not add user: {e}")

if not users_named:
    st.info("Please add a user from the sidebar to continue.")
    st.stop()

# Resolve selected user id and object
selected_user_id = None
selected_user_name = user_choice
for uid, nm in users_named:
    if nm == user_choice:
        selected_user_id = uid
        break

if selected_user_id is None:
    selected_user_id = users_named[0][0] if users_named else None

user = None
if session and User is not None and selected_user_id:
    try:
        user = session.query(User).filter_by(id=selected_user_id).first()
    except Exception:
        user = None

if user is None:
    user = {"id": selected_user_id, "name": selected_user_name}

st.header(f"Welcome, {user['name'] if isinstance(user, dict) else user.name}")

# -------------- Alerts: check recent critical readings --------------
try:
    from app_utils import parse_bp, parse_sugar
except Exception:
    def parse_bp(v): return str(v or "")
    def parse_sugar(v): return str(v or "")

recent_critical = []
now_utc = datetime.now(timezone.utc)
day_ago_utc = now_utc - timedelta(hours=24)
try:
    if session and HealthRecord is not None:
        recs_24 = session.query(HealthRecord).filter(HealthRecord.user_id==selected_user_id, HealthRecord.recorded_at >= day_ago_utc).all()
    elif agent and hasattr(agent, "list_health_records"):
        recs_24 = agent.list_health_records(selected_user_id, limit=500)
    elif db_module and hasattr(db_module, "list_health_records"):
        recs_24 = db_module.list_health_records(selected_user_id, limit=500)
    else:
        recs_24 = []
except Exception:
    recs_24 = []

for r in recs_24:
    try:
        r_type = r.type if not isinstance(r, dict) else r.get("type")
        r_value = r.value if not isinstance(r, dict) else r.get("value")
        if r_type == "bp":
            if "crisis" in parse_bp(r_value).lower() or "emergency" in parse_bp(r_value).lower():
                recent_critical.append((r, parse_bp(r_value)))
        if r_type == "sugar":
            if "emergency" in parse_sugar(r_value).lower() or "very high" in parse_sugar(r_value).lower() or "low" in parse_sugar(r_value).lower():
                recent_critical.append((r, parse_sugar(r_value)))
    except Exception:
        continue

if recent_critical:
    st.markdown("---")
    st.error("🚨 Recent critical readings detected. Check the Recent Health Records section for details.")

# ---------------- Add Medication form ----------------
st.subheader("Add Medication 💊")
with st.form("add_med_form_v1"):
    mname = st.text_input("Medication Name")
    dose = st.text_input("Dose (e.g., 1 tab, 75 mg)")
    time_input = st.time_input("Time to take", value=time(8, 0))
    freq = st.selectbox("Frequency", ["Daily", "Once", "Alternate Days"])
    notes = st.text_area("Notes (optional)")
    submit_med = st.form_submit_button("Add Medication")
    if submit_med:
<<<<<<< HEAD
        # at top of file where imports are (only once)
        # inside your Add Medication form submit code (replace or expand)
=======
>>>>>>> 6d768788236e5406ac5ab5cf55c6a3d4fcc57964
        tstr = time_input.strftime("%H:%M")
        if not mname.strip():
            st.error("Medication name is required.")
        elif not validate_dose(dose.strip()):
            st.error("Dose looks invalid (too long).")
        elif not validate_time_str(tstr):
            st.error("Time must be in HH:MM format.")
        else:
<<<<<<< HEAD
            # Build list of current medication names for this user
            try:
                if agent and hasattr(agent, "list_medications"):
                    existing = agent.list_medications(user['id'] if isinstance(user, dict) else user.id)
                    existing_names = [m.get("name") if isinstance(m, dict) else getattr(m, "name", "") for m in existing]
                elif db_module and hasattr(db_module, "list_medications"):
                    existing = db_module.list_medications(user_id=(user['id'] if isinstance(user, dict) else user.id))
                    existing_names = [r.get("name") for r in existing]
                elif session and Medication is not None:
                    existing = session.query(Medication).filter_by(user_id=(user['id'] if isinstance(user, dict) else user.id)).all()
                    existing_names = [getattr(m, "name", "") for m in existing]
                else:
                    existing_names = []
            except Exception:
                existing_names = []

            # Run interactions check between new med and existing meds
            interaction_warnings = di.scan_list(existing_names + [mname.strip()])  # it checks all pairs; we'll filter pairs involving new med
            new_warnings = [w for w in interaction_warnings if w["a"].lower() == mname.strip().lower() or w["b"].lower() == mname.strip().lower()]

            if new_warnings:
                st.warning("⚠ Potential interactions detected with this medication:")
                for w in new_warnings:
                    st.write(f"- *{w['a']}* ↔ *{w['b']}* — {w['severity'].upper()}: {w['desc']}")
                proceed = st.checkbox("I have reviewed the interaction(s) and want to add this medication anyway")
                if not proceed:
                    st.info("Medication not added. Check interactions or modify medication.")
                else:
                    # proceed to add (same code you used earlier)
                    try:
                        # ... add med via agent/db/session exactly as your existing code ...
                        if agent and hasattr(agent, "add_medication"):
                            medrec = agent.add_medication(user['id'] if isinstance(user, dict) else user.id, mname.strip(), dose.strip(), tstr, frequency=freq, notes=notes.strip() or None)
                            st.success(f"✅ Added {mname.strip()} at {tstr}")
                            st.rerun()

                        elif db_module and hasattr(db_module, "add_medication"):
                            db_module.add_medication(name=mname.strip(), dose=dose.strip(), times=tstr, user_id=(user['id'] if isinstance(user, dict) else user.id), frequency=freq, notes=notes.strip() or None)
                            st.success(f"✅ Added {mname.strip()} at {tstr}")
                            st.rerun()

                        elif session and Medication is not None:
                            med = Medication(user_id=(user['id'] if isinstance(user, dict) else user.id), name=mname.strip(), dose=dose.strip(), time=tstr, frequency=freq, notes=notes.strip())
                            session.add(med)
                            session.commit()
                            st.success(f"✅ Added {med.name} at {med.time}")
                            st.rerun()
                        else:
                            st.error("No DB backend is available to save the medication.")
                    except Exception as e:
                        st.error(f"Error adding medication: {e}")
            else:
                # no interactions, proceed normally (same add code as above)
                try:
                    if agent and hasattr(agent, "add_medication"):
                        medrec = agent.add_medication(user['id'] if isinstance(user, dict) else user.id, mname.strip(), dose.strip(), tstr, frequency=freq, notes=notes.strip() or None)
                        st.success(f"✅ Added {mname.strip()} at {tstr}")
                        
                        # ---- PERSIST INTERACTION ALERTS (A.3) ----
                        if new_warnings:
                            try:
                                uid_val = user['id'] if isinstance(user, dict) else user.id
                                if agent and hasattr(agent, "add_alert"):
                                    for w in new_warnings:
                                        agent.add_alert(
                                            user_id=uid_val,
                                            medication_a = w.get("a"),
                                            medication_b = w.get("b"),
                                            severity = w.get("severity", "moderate"),
                                            description = w.get("desc", "") or w.get("description", ""),
                                            note = "added via UI"
                                        )
                                elif db_module and hasattr(db_module, "add_alert"):
                                    for w in new_warnings:
                                        db_module.add_alert(
                                            user_id=uid_val,
                                            medication_a = w.get("a"),
                                            medication_b = w.get("b"),
                                            severity = w.get("severity", "moderate"),
                                            description = w.get("desc", "") or w.get("description", ""),
                                            note = "added via UI"
                                        )
                            except Exception as e:
                                st.warning(f"Could not store interaction alert(s): {e}")
                        st.rerun()
                    elif db_module and hasattr(db_module, "add_medication"):
                        db_module.add_medication(name=mname.strip(), dose=dose.strip(), times=tstr, user_id=(user['id'] if isinstance(user, dict) else user.id), frequency=freq, notes=notes.strip() or None)
                        st.success(f"✅ Added {mname.strip()} at {tstr}")
                        # ---- PERSIST INTERACTION ALERTS (A.3) ----
                        if new_warnings:
                            try:
                                uid_val = user['id'] if isinstance(user, dict) else user.id
                                if agent and hasattr(agent, "add_alert"):
                                    for w in new_warnings:
                                        agent.add_alert(
                                            user_id=uid_val,
                                            medication_a = w.get("a"),
                                            medication_b = w.get("b"),
                                            severity = w.get("severity", "moderate"),
                                            description = w.get("desc", "") or w.get("description", ""),
                                            note = "added via UI"
                                        )
                                elif db_module and hasattr(db_module, "add_alert"):
                                    for w in new_warnings:
                                        db_module.add_alert(
                                            user_id=uid_val,
                                            medication_a = w.get("a"),
                                            medication_b = w.get("b"),
                                            severity = w.get("severity", "moderate"),
                                            description = w.get("desc", "") or w.get("description", ""),
                                            note = "added via UI"
                                        )
                            except Exception as e:
                                st.warning(f"Could not store interaction alert(s): {e}")
                        

                        st.rerun()
                    elif session and Medication is not None:
                        med = Medication(user_id=(user['id'] if isinstance(user, dict) else user.id), name=mname.strip(), dose=dose.strip(), time=tstr, frequency=freq, notes=notes.strip())
                        session.add(med)
                        session.commit()
                        st.success(f"✅ Added {med.name} at {med.time}")
                        st.rerun()
                    else:
                        st.error("No DB backend is available to save the medication.")
                except Exception as e:
                    st.error(f"Error adding medication: {e}")

=======
            try:
                if agent and hasattr(agent, "add_medication"):
                    medrec = agent.add_medication(user['id'] if isinstance(user, dict) else user.id, mname.strip(), dose.strip(), tstr, frequency=freq, notes=notes.strip() or None)
                    st.success(f"✅ Added {mname.strip()} at {tstr}")
                    st.rerun()
                elif db_module and hasattr(db_module, "add_medication"):
                    db_module.add_medication(name=mname.strip(), dose=dose.strip(), times=tstr, user_id=(user['id'] if isinstance(user, dict) else user.id), frequency=freq, notes=notes.strip() or None)
                    st.success(f"✅ Added {mname.strip()} at {tstr}")
                    st.rerun()
                elif session and Medication is not None:
                    med = Medication(user_id=(user['id'] if isinstance(user, dict) else user.id), name=mname.strip(), dose=dose.strip(), time=tstr, frequency=freq, notes=notes.strip())
                    session.add(med)
                    session.commit()
                    st.success(f"✅ Added {med.name} at {med.time}")
                    st.rerun()
                else:
                    st.error("No DB backend is available to save the medication.")
            except Exception as e:
                st.error(f"Error adding medication: {e}")

>>>>>>> 6d768788236e5406ac5ab5cf55c6a3d4fcc57964
# ---------------- Medication List + actions (Day 7 step 3) ----------------
st.subheader("📋 Medication List")
try:
    if agent and hasattr(agent, "list_medications"):
        meds = agent.list_medications(user['id'] if isinstance(user, dict) else user.id)
    elif db_module and hasattr(db_module, "list_medications"):
        meds = db_module.list_medications(user_id=(user['id'] if isinstance(user, dict) else user.id))
    elif session and Medication is not None:
        meds = session.query(Medication).filter_by(user_id=(user['id'] if isinstance(user, dict) else user.id)).all()
    else:
        meds = []
except Exception:
    meds = []

if meds:
    for m in meds:
        # unify fields for dict or ORM object
        med_id = m.get("id") if isinstance(m, dict) else getattr(m, "id", None)
        name   = m.get("name") if isinstance(m, dict) else getattr(m, "name", "")
        dose   = m.get("dose") if isinstance(m, dict) else getattr(m, "dose", "")
        times  = m.get("times") if isinstance(m, dict) else getattr(m, "time", "")
        freq   = m.get("frequency") if isinstance(m, dict) else getattr(m, "frequency", "")
        created_at = m.get("created_at") if isinstance(m, dict) else None

        c1, c2, c3 = st.columns([6,1,1])
        c1.write(f"{name}** — {dose or ''} at {times} ({freq})")
        if created_at:
            c1.caption(f"added: {created_at}")

        # recent "taken" count (if med_taken table and helpers exist)
        taken_count = 0
        try:
            if agent and hasattr(agent, "list_med_taken"):
                taken_rows = agent.list_med_taken(user['id'] if isinstance(user, dict) else user.id, medication_id=med_id, limit=5)
            elif db_module and hasattr(db_module, "list_med_taken"):
                taken_rows = db_module.list_med_taken(user['id'] if isinstance(user, dict) else user.id, medication_id=med_id, limit=5)
            else:
                taken_rows = []
            taken_count = len(taken_rows) if taken_rows else 0
        except Exception:
            taken_count = 0

        if taken_count:
            c1.caption(f"Taken {taken_count} time(s) recently")

        # Mark as taken (✓)
        if c2.button("✓", key=f"take-{med_id}"):
            try:
                if agent and hasattr(agent, "add_med_taken"):
                    agent.add_med_taken(user['id'] if isinstance(user, dict) else user.id, med_id, taken_at=datetime.now(timezone.utc).isoformat(), note="marked via UI")
                elif db_module and hasattr(db_module, "add_med_taken"):
                    db_module.add_med_taken(user['id'] if isinstance(user, dict) else user.id, med_id, taken_at=datetime.now(timezone.utc).isoformat(), note="marked via UI")
                else:
                    # fallback: no med_taken backend
                    raise RuntimeError("No med_taken backend available")
                st.success("Marked as taken ✅")
                st.rerun()
            except Exception as e:
                st.error(f"Could not record taken event: {e}")

        # Delete button
        if c3.button("🗑", key=f"del-{med_id}"):
            try:
                if agent and hasattr(agent, "delete_medication"):
                    ok = agent.delete_medication(med_id)
                elif db_module and hasattr(db_module, "delete_medication"):
                    ok = db_module.delete_medication(med_id)
                elif session and Medication is not None:
                    # ORM deletion
                    if isinstance(m, dict):
                        ok = False
                    else:
                        session.delete(m)
                        session.commit()
                        ok = True
                else:
                    ok = False

                if ok:
                    st.warning(f"Deleted {name}")
                    st.rerun()
                else:
                    st.error("Could not delete medication (not found).")
            except Exception as e:
                st.error(f"Error deleting medication: {e}")
else:
    st.info("No medications found.")

<<<<<<< HEAD
st.markdown("---")
st.subheader("🔎 Medication Interaction Scan")
st.subheader("⚠️ Interaction Alerts")
try:
    if agent and hasattr(agent, "list_alerts"):
        alerts = agent.list_alerts(user['id'] if isinstance(user, dict) else user.id)
    elif db_module and hasattr(db_module, "list_alerts"):
        alerts = db_module.list_alerts(user['id'] if isinstance(user, dict) else user.id)
    else:
        alerts = []
except Exception:
    alerts = []

if not alerts:
    st.info("No stored alerts.")
else:
    for a in alerts:
        created = fmt_dt_for_display(a.get("created_at"))
        st.write(f"- {a.get('medication_a')} ↔ {a.get('medication_b')} | {a.get('severity').upper()} — {a.get('description') or a.get('note','')} (recorded {created})")

# Get current meds names
try:
    if agent and hasattr(agent, "list_medications"):
        cur_meds = agent.list_medications(user['id'] if isinstance(user, dict) else user.id)
        cur_names = [m.get("name") if isinstance(m, dict) else getattr(m, "name","") for m in cur_meds]
    elif db_module and hasattr(db_module, "list_medications"):
        cur_meds = db_module.list_medications(user_id=(user['id'] if isinstance(user, dict) else user.id))
        cur_names = [r.get("name") for r in cur_meds]
    elif session and Medication is not None:
        cur = session.query(Medication).filter_by(user_id=(user['id'] if isinstance(user, dict) else user.id)).all()
        cur_names = [getattr(m, "name","") for m in cur]
    else:
        cur_names = []
except Exception:
    cur_names = []

if not cur_names:
    st.info("No medications to scan.")
else:
    st.write("Current medications:")
    for nm in cur_names:
        st.write(f"- {nm}")
    scan_btn = st.button("Run interaction scan")
    if scan_btn:
        results = di.scan_list(cur_names)
        if not results:
            st.success("✅ No known interactions found for listed medications (based on local DB).")
        else:
            st.warning(f"⚠ Found {len(results)} interaction(s):")
            # sort by severity (high first)
            severity_order = {"high": 3, "moderate": 2, "mild": 1}
            results = sorted(results, key=lambda x: -severity_order.get(x.get("severity","moderate"), 2))
            for r in results:
                st.write(f"- *{r['a']}* ↔ *{r['b']}* — {r['severity'].upper()}: {r['desc']}")
            st.write("If you see important interactions, consult a clinician before taking both drugs together.")

=======
>>>>>>> 6d768788236e5406ac5ab5cf55c6a3d4fcc57964
# ---------------- Fitness / Activity (Day 4) ----------------
st.markdown("---")
st.subheader("🏃 Fitness / Activity")

with st.form("add_fitness_form_v1"):
    f_steps = st.number_input("Steps (today)", min_value=0, value=0, step=1, key="fit_steps")
    f_cal = st.number_input("Calories burned (optional)", min_value=0, value=0, step=1, key="fit_cal")
    f_date = st.date_input("Record date (optional)", value=datetime.now().date(), key="fit_date")
    f_time = st.time_input("Record time (optional)", value=datetime.now().time().replace(second=0, microsecond=0), key="fit_time")
    f_notes = st.text_area("Notes (optional)", key="fit_notes")
    add_fit = st.form_submit_button("Save Fitness Record")

if add_fit:
    record_dt = datetime.combine(f_date, f_time)
    # Save as ISO (UTC-naive -> will be assumed UTC by db module)
    rec_iso = record_dt.replace(tzinfo=timezone.utc).isoformat() if record_dt.tzinfo is None else record_dt.isoformat()
    try:
        if agent and hasattr(agent, "add_fitness_record"):
            agent.add_fitness_record(user_id=(user['id'] if isinstance(user, dict) else user.id), steps=int(f_steps) if f_steps else None, calories=int(f_cal) if f_cal else None, record_date=rec_iso, notes=(f_notes.strip() or None))
        elif db_module and hasattr(db_module, "add_fitness_record"):
            db_module.add_fitness_record(user_id=(user['id'] if isinstance(user, dict) else user.id), steps=int(f_steps) if f_steps else None, calories=int(f_cal) if f_cal else None, record_date=rec_iso, notes=(f_notes.strip() or None))
        elif session and FitnessRecord is not None:
            rec = FitnessRecord(user_id=(user['id'] if isinstance(user, dict) else user.id), steps=int(f_steps) if f_steps else None, calories=int(f_cal) if f_cal else None, date=rec_iso, notes=(f_notes.strip() or None))
            session.add(rec)
            session.commit()
<<<<<<< HEAD
=======
        else:
            st.error("No backend available to save fitness record.")
        st.success("✅ Fitness record saved.")
        st.rerun()
    except Exception as e:
        st.error(f"Error saving fitness record: {e}")

# CSV import for fitness (optional)
st.markdown("Import fitness from CSV (optional) — columns: date,steps,calories")
csv_file = st.file_uploader("Upload CSV", type=["csv"], key="fit_csv")
if csv_file is not None:
    try:
        df_csv = pd.read_csv(csv_file)
        count = 0
        for _, row in df_csv.iterrows():
            rd = None
            if "date" in row and not pd.isna(row["date"]):
                rd = str(row["date"])
            steps = int(row["steps"]) if ("steps" in row and not pd.isna(row["steps"])) else None
            calories = int(row["calories"]) if ("calories" in row and not pd.isna(row["calories"])) else None
            rec_date_iso = None
            if rd:
                try:
                    rec_dt = pd.to_datetime(rd, errors="coerce")
                    if not pd.isna(rec_dt):
                        rec_date_iso = rec_dt.to_pydatetime().isoformat()
                except Exception:
                    rec_date_iso = None
            if agent and hasattr(agent, "add_fitness_record"):
                agent.add_fitness_record(user_id=(user['id'] if isinstance(user, dict) else user.id), steps=steps, calories=calories, record_date=rec_date_iso, notes="imported-csv")
            elif db_module and hasattr(db_module, "add_fitness_record"):
                db_module.add_fitness_record(user_id=(user['id'] if isinstance(user, dict) else user.id), steps=steps, calories=calories, record_date=rec_date_iso, notes="imported-csv")
            count += 1
        st.success(f"Imported {count} rows.")
        st.rerun()
    except Exception as e:
        st.error(f"CSV import failed: {e}")

# Show recent fitness logs
st.markdown("---")
st.subheader("Recent fitness logs:")

try:
    if agent and hasattr(agent, "list_fitness_records"):
        fit_recs = agent.list_fitness_records(user['id'] if isinstance(user, dict) else user.id, limit=30)
    elif db_module and hasattr(db_module, "list_fitness_records"):
        fit_recs = db_module.list_fitness_records(user_id=(user['id'] if isinstance(user, dict) else user.id), limit=30)
    elif session and FitnessRecord is not None:
        fit_recs = session.query(FitnessRecord).filter_by(user_id=(user['id'] if isinstance(user, dict) else user.id)).order_by(FitnessRecord.date.desc()).limit(30).all()
    else:
        fit_recs = []
except Exception:
    fit_recs = []

if not fit_recs:
    st.info("No fitness records yet. Add one above.")
else:
    disp_rows = []
    for r in fit_recs:
        if isinstance(r, dict):
            rec_date = r.get("record_date") or r.get("date") or r.get("recorded_at")
            steps = r.get("steps") or 0
            notes = r.get("notes") or ""
        else:
            rec_date = getattr(r, "date", None) or getattr(r, "record_date", None) or getattr(r, "recorded_at", None)
            steps = getattr(r, "steps", 0) or 0
            notes = getattr(r, "notes", "") or ""
        if isinstance(rec_date, str):
            disp_date = rec_date
        else:
            try:
                disp_date = pd.to_datetime(rec_date, errors="coerce").to_pydatetime().isoformat()
            except Exception:
                disp_date = str(rec_date)
        disp_rows.append({"date": disp_date, "steps": steps})
        st.write(f"- {disp_date} — Steps: {steps} {(' — ' + notes) if notes else ''}")

    try:
        avg_steps = int(pd.Series([r["steps"] for r in disp_rows]).mean()) if disp_rows else 0
        st.write(f"Average steps (shown range): {avg_steps}")
    except Exception:
        pass

    df = pd.DataFrame(disp_rows)
    if not df.empty:
        df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.set_index("date_parsed").sort_index()
        st.line_chart(df["steps"])

# ---------------- Health Record Form ----------------
st.markdown("---")
st.subheader("Add Health Record 🩺")
with st.form("add_health_form_v1"):
    htype = st.selectbox("Type", ["bp", "sugar", "weight"])
    hvalue = st.text_input("Value (e.g., BP: 120/80  |  Sugar: 110)")
    hnotes = st.text_area("Notes")
    add_health = st.form_submit_button("Add Record")
    if add_health:
        if hvalue.strip():
            try:
                if agent and hasattr(agent, "add_health_record"):
                    agent.add_health_record(user_id=(user['id'] if isinstance(user, dict) else user.id), type_=htype, value=hvalue.strip(), notes=hnotes.strip() or None)
                elif db_module and hasattr(db_module, "add_health_record"):
                    db_module.add_health_record(user_id=(user['id'] if isinstance(user, dict) else user.id), type_=htype, value=hvalue.strip(), notes=hnotes.strip() or None)
                elif session and HealthRecord is not None:
                    rec = HealthRecord(user_id=(user['id'] if isinstance(user, dict) else user.id), type=htype, value=hvalue.strip(), notes=hnotes.strip() or None)
                    session.add(rec)
                    session.commit()
                else:
                    st.error("No backend available to save health record.")
                st.success("✅ Health record added!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving health record: {e}")
>>>>>>> 6d768788236e5406ac5ab5cf55c6a3d4fcc57964
        else:
            st.error("No backend available to save fitness record.")
        st.success("✅ Fitness record saved.")
        st.rerun()
    except Exception as e:
        st.error(f"Error saving fitness record: {e}")

<<<<<<< HEAD
# CSV import for fitness (optional)
st.markdown("Import fitness from CSV (optional) — columns: date,steps,calories")
csv_file = st.file_uploader("Upload CSV", type=["csv"], key="fit_csv")
if csv_file is not None:
    try:
        df_csv = pd.read_csv(csv_file)
        count = 0
        for _, row in df_csv.iterrows():
            rd = None
            if "date" in row and not pd.isna(row["date"]):
                rd = str(row["date"])
            steps = int(row["steps"]) if ("steps" in row and not pd.isna(row["steps"])) else None
            calories = int(row["calories"]) if ("calories" in row and not pd.isna(row["calories"])) else None
            rec_date_iso = None
            if rd:
                try:
                    rec_dt = pd.to_datetime(rd, errors="coerce")
                    if not pd.isna(rec_dt):
                        rec_date_iso = rec_dt.to_pydatetime().isoformat()
                except Exception:
                    rec_date_iso = None
            if agent and hasattr(agent, "add_fitness_record"):
                agent.add_fitness_record(user_id=(user['id'] if isinstance(user, dict) else user.id), steps=steps, calories=calories, record_date=rec_date_iso, notes="imported-csv")
            elif db_module and hasattr(db_module, "add_fitness_record"):
                db_module.add_fitness_record(user_id=(user['id'] if isinstance(user, dict) else user.id), steps=steps, calories=calories, record_date=rec_date_iso, notes="imported-csv")
            count += 1
        st.success(f"Imported {count} rows.")
        st.rerun()
    except Exception as e:
        st.error(f"CSV import failed: {e}")

#--------------------------- Show recent fitness logs
st.markdown("---")
st.subheader("Recent fitness logs:")

try:
    if agent and hasattr(agent, "list_fitness_records"):
        fit_recs = agent.list_fitness_records(user['id'] if isinstance(user, dict) else user.id, limit=30)
    elif db_module and hasattr(db_module, "list_fitness_records"):
        fit_recs = db_module.list_fitness_records(user_id=(user['id'] if isinstance(user, dict) else user.id), limit=30)
    elif session and FitnessRecord is not None:
        fit_recs = session.query(FitnessRecord).filter_by(user_id=(user['id'] if isinstance(user, dict) else user.id)).order_by(FitnessRecord.date.desc()).limit(30).all()
    else:
        fit_recs = []
except Exception:
    fit_recs = []

if not fit_recs:
    st.info("No fitness records yet. Add one above.")
else:
    disp_rows = []
    for r in fit_recs:
        if isinstance(r, dict):
            rec_date = r.get("record_date") or r.get("date") or r.get("recorded_at")
            steps = r.get("steps") or 0
            notes = r.get("notes") or ""
        else:
            rec_date = getattr(r, "date", None) or getattr(r, "record_date", None) or getattr(r, "recorded_at", None)
            steps = getattr(r, "steps", 0) or 0
            notes = getattr(r, "notes", "") or ""
        if isinstance(rec_date, str):
            disp_date = rec_date
        else:
            try:
                disp_date = pd.to_datetime(rec_date, errors="coerce").to_pydatetime().isoformat()
            except Exception:
                disp_date = str(rec_date)
        disp_rows.append({"date": disp_date, "steps": steps})
        st.write(f"- {disp_date} — Steps: {steps} {(' — ' + notes) if notes else ''}")

    try:
        avg_steps = int(pd.Series([r["steps"] for r in disp_rows]).mean()) if disp_rows else 0
        st.write(f"Average steps (shown range): {avg_steps}")
    except Exception:
        pass

    df = pd.DataFrame(disp_rows)
    if not df.empty:
        df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.set_index("date_parsed").sort_index()
        st.line_chart(df["steps"])

# ---------------- Goals: create & track ----------------
st.markdown("---")
st.subheader("🎯 Goals & Progress")

# Add new goal form
with st.form("add_goal_form"):
    g_title = st.text_input("Goal title (e.g., 'Daily steps target')")
    g_type = st.selectbox("Goal type", ["steps_daily", "weight_target"], help="steps_daily = daily steps target; weight_target = target weight")
    g_target = st.number_input("Target value (numeric)", min_value=0.0, value=10000.0)
    g_unit = st.text_input("Unit (e.g., steps, kg)", value="steps")
    g_start = st.date_input("Start date", value=datetime.now().date())
    g_end = st.date_input("End date (optional)", value=None)
    g_notes = st.text_area("Notes (optional)")
    add_goal_btn = st.form_submit_button("Create Goal")
    if add_goal_btn:
        try:
            uid = user['id'] if isinstance(user, dict) else user.id
            # call agent or db_module using the expected keyword names
            if agent and hasattr(agent, "add_goal"):
                agent.add_goal(
                    user_id=uid,
                    goal_title=g_title,
                    goal_type=g_type,
                    target_value=g_target,
                    unit=g_unit,
                    start_date=str(g_start),   # store as string YYYY-MM-DD or convert as you prefer
                    end_date=str(g_end) if g_end else None,
                    notes=g_notes
                )
            elif db_module and hasattr(db_module, "add_goal"):
                db_module.add_goal(
                    user_id=uid,
                    goal_title=g_title,
                    goal_type=g_type,
                    target_value=g_target,
                    unit=g_unit,
                    start_date=str(g_start),
                    end_date=str(g_end) if g_end else None,
                    notes=g_notes
                )
            st.success("✅ Goal created.")
            st.rerun()
        except Exception as e:
            st.error(f"Could not create goal: {e}")

# List goals and compute progress

# List goals and compute progress
try:
    uid_val = user['id'] if isinstance(user, dict) else user.id
    goals = []

    # 1) Try agent.list_goals (but don't let it break the flow)
    try:
        if agent and hasattr(agent, "list_goals"):
            maybe = agent.list_goals(uid_val)
            goals = maybe or []
    except Exception as exc:
        # show a non-fatal warning in UI (optional) and continue to next option
        st.warning(f"Agent list_goals error (ignored): {exc}")
        goals = []

    # 2) If still empty, try db_module.list_goals
    if not goals:
        try:
            if db_module and hasattr(db_module, "list_goals"):
                maybe = db_module.list_goals(uid_val)
                goals = maybe or []
        except Exception as exc:
            st.warning(f"db_module.list_goals error (ignored): {exc}")
            goals = []

    # 3) FINAL FALLBACK: read directly from sqlite database if nothing found yet
    if not goals:
        import sqlite3, os
        DB_FILE = os.getenv("DB_PATH", r"C:\Users\chand\desktop\health-ai-agent\health.db")
        DB_FILE = os.path.abspath(DB_FILE)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, goal_title, goal_type, target_value, unit, start_date, end_date, notes
            FROM goals
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (uid_val,))
        goals = [dict(r) for r in cur.fetchall()]
        conn.close()

except Exception as e:
    st.error(f"Could not load goals: {e}")
    goals = []
    
if not goals:
    st.info("No goals yet. Add one above.")
else:
    for g in goals:
        gid = g.get("id") if isinstance(g, dict) else getattr(g, "id", None)
        goal_title = g.get("goal_title") if isinstance(g, dict) else getattr(g, "goal_title", "")
        gtype = g.get("goal_type") if isinstance(g, dict) else getattr(g, "goal_type", "")
        target = g.get("target_value") if isinstance(g, dict) else getattr(g, "target_value", None)
        unit = g.get("unit") if isinstance(g, dict) else getattr(g, "unit", "")
        sdate = g.get("start_date") if isinstance(g, dict) else getattr(g, "start_date", None)
        edate = g.get("end_date") if isinstance(g, dict) else getattr(g, "end_date", None)

        # compute progress (example implementations)
        progress_pct = None
        progress_display = "—"

        if gtype == "steps_daily":
            # compute average steps over last 7 days and compare to daily target
            try:
                # reuse existing steps_records fetch (or query db)
                import pandas as _pd
                if agent and hasattr(agent, "list_fitness_records"):
                    recs = agent.list_fitness_records(user['id'] if isinstance(user, dict) else user.id, limit=30)
                    steps_list = []
                    for r in recs:
                        steps_val = (r.get("steps") if isinstance(r, dict) else getattr(r, "steps", None))
                        if steps_val is not None:
                            steps_list.append(int(steps_val))
                    avg = int(_pd.Series(steps_list).mean()) if steps_list else 0
                elif db_module and hasattr(db_module, "list_fitness_records"):
                    recs = db_module.list_fitness_records(user_id=(user['id'] if isinstance(user, dict) else user.id), limit=30)
                    steps_list = [int(r.get("steps")) for r in recs if r.get("steps") is not None]
                    avg = int(_pd.Series(steps_list).mean()) if steps_list else 0
                else:
                    avg = 0
                if target and target > 0:
                    progress_pct = min(100, int((avg / float(target)) * 100))
                    progress_display = f"{avg} / {int(target)} {unit} ({progress_pct}%)"
                else:
                    progress_display = f"{avg} {unit}"
            except Exception:
                progress_display = "N/A"
        elif gtype == "weight_target":
            # get latest weight record and compute distance to target
            try:
                if agent and hasattr(agent, "list_health_records"):
                    recs = agent.list_health_records(user['id'] if isinstance(user, dict) else user.id, record_type="weight", limit=10)
                    latest = None
                    for r in recs:
                        latest = r if isinstance(r, dict) else {"value": getattr(r, "value", None)}
                        break
                    latest_val = float(latest.get("value")) if latest and latest.get("value") else None
                elif db_module and hasattr(db_module, "list_health_records"):
                    recs = db_module.list_health_records(user_id=(user['id'] if isinstance(user, dict) else user.id), record_type="weight", limit=10)
                    latest_val = float(recs[0].get("value")) if recs else None
                else:
                    latest_val = None
                if latest_val is not None and target:
                    # progress: percent closer to target from start (simple)
                    diff = abs(latest_val - float(target))
                    progress_display = f"Latest: {latest_val}{unit} — Target: {target}{unit} (diff {diff}{unit})"
                else:
                    progress_display = "No weight records yet."
            except Exception:
                progress_display = "N/A"
        else:
            progress_display = "Progress tracking not implemented for this goal type."

        # render
        st.write(f"**{goal_title}** — {gtype} — Target: {target} {unit}")
        st.caption(f"Start: {sdate or '—'}  End: {edate or '—'}")
        st.info(f"Progress: {progress_display}")

        # action buttons
        col1, col2, col3 = st.columns([1,1,4])
        if col1.button("Edit", key=f"edit_goal_{gid}"):
            st.toast("Edit not wired in quick UI — use backend or update later.")
        if col2.button("Delete", key=f"del_goal_{gid}"):
            try:
                if agent and hasattr(agent, "delete_goal"):
                    agent.delete_goal(gid)
                elif db_module and hasattr(db_module, "delete_goal"):
                    db_module.delete_goal(gid)
                st.success("Goal deleted.")
                st.rerun()
            except Exception as e:
                st.error(f"Could not delete goal: {e}")
# ----- Medication Interaction Checker (India DB) -----
import streamlit as st
from meds_db import search_med, get_med_by_id, check_interaction_by_names

DB_PATH = "meds_india.db"

st.markdown("### 💊 Medication Interaction Checker (India DB)")

# quick search + select helper
def pick_med(label):
    q = st.text_input(f"Search med for {label}", value="", key=f"q_{label}")
    sel = None
    if q:
        results = search_med(DB_PATH, q, limit=20)
        names = []
        for r in results:
            display = r.get("name") or ""
            # include brand/generic if present
            if r.get("brand"):
                display += f" ({r.get('brand')})"
            elif r.get("generic"):
                display += f" ({r.get('generic')})"
            names.append(f'{r["id"]}: {display}')
        if names:
            chosen = st.selectbox(f"Select {label}", ["-- choose --"] + names, key=f"sel_{label}")
            if chosen and chosen != "-- choose --":
                sel_id = int(chosen.split(":")[0])
                sel = get_med_by_id(DB_PATH, sel_id)
    return sel

col1, col2 = st.columns(2)
with col1:
    med_a = pick_med("A")
with col2:
    med_b = pick_med("B")

if st.button("Check Interaction"):
    if not med_a or not med_b:
        st.error("Please pick two medications (A and B) to check.")
    else:
        # Try direct DB interactions first
        res = None
        try:
            res = check_interaction_by_names(DB_PATH, med_a.get("name",""), med_b.get("name",""))
        except Exception as e:
            st.error("Interaction lookup failed: " + str(e))

        if not res:
            st.success("No known interaction found in the local ruleset. Always verify with clinician.")
        else:
            sev = res.get("severity")
            msg = res.get("description") or ""
            # normalize severity strings
            if sev and sev.lower() in ("danger","contraindicated","contra"):
                st.error(f"⚠️ CONTRAINDICATED: {msg}")
            elif sev and sev.lower() in ("warn","warning"):
                st.warning(f"⚠️ WARNING: {msg}")
            else:
                st.info(f"ℹ️ Info: {msg}")
# ---------------- Unified Health Record Form + Recent Records ----------------
import traceback
from datetime import datetime

def _get_user_id(user):
    try:
        return user['id'] if isinstance(user, dict) else user.id
    except Exception:
        return 1  # fallback for local/demo

def _save_record_backend(user_id, type_, value, notes):
    """Try available backends in safe order. Return (ok, message)."""
    try:
        if agent and hasattr(agent, "add_health_record"):
            agent.add_health_record(user_id=user_id, type_=type_, value=value, notes=notes)
            return True, "Saved via agent"
        if db_module and hasattr(db_module, "add_health_record"):
            db_module.add_health_record(user_id=user_id, type_=type_, value=value, notes=notes)
            return True, "Saved via db_module"
        if 'session' in globals() and HealthRecord is not None:
            rec = HealthRecord(user_id=user_id, type=type_, value=value, notes=notes)
            session.add(rec)
            session.commit()
            return True, "Saved via SQLAlchemy session"
    except Exception as e:
        return False, f"Exception saving record: {e}"
    return False, "No backend available to save health record."

def _safe_call_parse_bp(val):
    try:
        if 'parse_bp' in globals() and callable(parse_bp):
            return parse_bp(val)
    except Exception:
        pass
    # fallback simple parse
    if isinstance(val, str) and "/" in val:
        return f"BP: {val}"
    return str(val)

def _safe_call_parse_sugar(val):
    try:
        if 'parse_sugar' in globals() and callable(parse_sugar):
            return parse_sugar(val)
    except Exception:
        pass
    return str(val)

def _fmt_dt(v):
    try:
        if 'fmt_dt_for_display' in globals() and callable(fmt_dt_for_display):
            return fmt_dt_for_display(v)
    except Exception:
        pass
    # fallback
    try:
        if isinstance(v, str):
            return v
        if isinstance(v, (int,float)):
            return datetime.fromtimestamp(v).isoformat()
        if hasattr(v, 'isoformat'):
            return v.isoformat()
    except Exception:
        pass
    return str(v)

# Single form for adding records
st.markdown("---")
st.subheader("Add / View Health Records 🩺")

with st.form("add_health_single_form"):
    htype = st.selectbox("Type", ["bp", "sugar", "weight"])
    if htype == "bp":
        hvalue = st.text_input("Value (e.g., 120/80)")
    elif htype == "sugar":
        hvalue = st.text_input("Value (mg/dL) (e.g., 110)")
    else:  # weight
        hvalue = st.text_input("Value (kg) (e.g., 72.5)")
    hnotes = st.text_area("Notes (optional)", height=80)
    add_health = st.form_submit_button("Add Record")

    if add_health:
        # validations
        if not hvalue or not hvalue.strip():
            st.error("Please enter a value.")
        else:
            uid = _get_user_id(user)
            ok, msg = _save_record_backend(uid, htype, hvalue.strip(), (hnotes.strip() or None))
            if ok:
                st.success("✅ Health record added!")
                # small optional debug info (won't raise)
                st.caption(msg)
                # rerun to refresh record listing
                st.rerun()
            else:
                st.error(f"Could not save record: {msg}")

# --------------------Show recent health records (single listing below the same form)
st.markdown("---")
st.subheader("Recent Health Records 🧾")

uid = _get_user_id(user)
records = []
try:
    if agent and hasattr(agent, "list_health_records"):
        records = agent.list_health_records(uid, limit=30)
    elif db_module and hasattr(db_module, "list_health_records"):
        records = db_module.list_health_records(user_id=uid, limit=30)
    elif 'session' in globals() and HealthRecord is not None:
        records = session.query(HealthRecord).filter_by(user_id=uid).order_by(HealthRecord.recorded_at.desc()).limit(30).all()
    else:
        records = []
except Exception as e:
    st.error("Error fetching health records (backend).")
    # log trace to console only
    print("Error fetching records:", e)
    traceback.print_exc()
=======
# ---------------- Show recent health records ----------------
st.markdown("---")
st.subheader("Recent Health Records 🧾")

try:
    if agent and hasattr(agent, "list_health_records"):
        records = agent.list_health_records(user['id'] if isinstance(user, dict) else user.id, limit=20)
    elif db_module and hasattr(db_module, "list_health_records"):
        records = db_module.list_health_records(user_id=(user['id'] if isinstance(user, dict) else user.id), limit=20)
    elif session and HealthRecord is not None:
        records = session.query(HealthRecord).filter_by(user_id=(user['id'] if isinstance(user, dict) else user.id)).order_by(HealthRecord.recorded_at.desc()).limit(20).all()
    else:
        records = []
except Exception:
>>>>>>> 6d768788236e5406ac5ab5cf55c6a3d4fcc57964
    records = []

if not records:
    st.info("No health records yet.")
else:
<<<<<<< HEAD
    # render as nice table-like list
    for r in records:
        try:
            # support dict-like and object-like rows
            is_dict = isinstance(r, dict)
            typ = r.get("type") if is_dict else getattr(r, "type", None)
            value = r.get("value") if is_dict else getattr(r, "value", None)
            notes = r.get("notes") if is_dict else getattr(r, "notes", None)
            # timestamp field variations
            recorded_at = None
            if is_dict:
                recorded_at = r.get("recorded_at") or r.get("created_at") or r.get("date")
            else:
                recorded_at = getattr(r, "recorded_at", None) or getattr(r, "created_at", None) or getattr(r, "date", None)

            ts = _fmt_dt(recorded_at)

            # classification and extra info
            extra = ""
            alert = None
            try:
                if typ == "bp":
                    extra = _safe_call_parse_bp(value)
                    if isinstance(extra, str) and any(k in extra.lower() for k in ("crisis", "emergency")):
                        alert = f"⚠️ {extra}"
                elif typ == "sugar":
                    extra = _safe_call_parse_sugar(value)
                    if isinstance(extra, str) and any(k in extra.lower() for k in ("emergency","very high","low")):
                        alert = f"⚠️ {extra}"
                elif typ == "weight":
                    extra = f"{value}"
                else:
                    extra = str(value)
            except Exception:
                extra = str(value)

            # build display line
            note_text = f" — {notes}" if notes else ""
            display = f"- {typ.upper() if typ else 'REC'} | {value} | {extra} | {ts}{note_text}"

            # show
            if alert:
                st.warning(display)
                st.error(alert)
            else:
                st.write(display)
        except Exception as e:
            # don't break loop; show minimal fallback
            st.write(f"- Error rendering record: {e}")
            print("render record error:", e)
            traceback.print_exc()

st.markdown("---")


# ----------------  Basic health-data analysis & charts ----------------
=======
    for r in records:
        ts = fmt_dt_for_display(r.recorded_at if not isinstance(r, dict) else r.get("recorded_at"))
        note = f" — {r.notes}" if (not isinstance(r, dict) and getattr(r, "notes", None)) else (f" — {r.get('notes')}" if isinstance(r, dict) and r.get("notes") else "")
        extra = ""
        alert = None

        # classify reading
        try:
            value = r.value if not isinstance(r, dict) else r.get("value")
            typ = r.type if not isinstance(r, dict) else r.get("type")
            if typ == "bp":
                extra = parse_bp(value)
                if "crisis" in extra.lower() or "emergency" in extra.lower():
                    alert = f"⚠ {extra}"
            elif typ == "sugar":
                extra = parse_sugar(value)
                if "emergency" in extra.lower() or "very high" in extra.lower() or "low" in extra.lower():
                    alert = f"⚠ {extra}"
            elif typ == "weight":
                extra = f"{value}"
        except Exception:
            extra = ""

        display = f"- {typ.upper() if 'typ' in locals() else 'REC'} | {value} | {extra} | {ts}{note}"
        if alert:
            st.warning(display)
            st.error(alert)
        else:
            st.write(display)

# ---------------- Day 5: Basic health-data analysis & charts ----------------
>>>>>>> 6d768788236e5406ac5ab5cf55c6a3d4fcc57964
st.markdown("---")
st.subheader("📊 Health analytics (last 7 days)")

import math
from datetime import timedelta as _timedelta

now = datetime.now(timezone.utc)
seven_days_ago = now - _timedelta(days=7)

# small helpers to parse numbers and BP
def extract_bp(bp_str):
    if not bp_str or not isinstance(bp_str, str):
        return None, None
    try:
        parts = bp_str.replace(" ", "").split("/")
        if len(parts) >= 2:
            s = int(''.join(ch for ch in parts[0] if ch.isdigit()))
            d = int(''.join(ch for ch in parts[1] if ch.isdigit()))
            return s, d
    except Exception:
        pass
    return None, None

def extract_number(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return val
    try:
        s = ''.join(ch for ch in str(val) if (ch.isdigit() or ch == '.' or ch == '-'))
        if s == '' or s == '-' or s == '.':
            return None
        return float(s) if '.' in s else int(float(s))
    except Exception:
        return None

def to_dt(obj):
    if obj is None:
        return None
    if isinstance(obj, str):
        try:
            return pd.to_datetime(obj, errors="coerce").to_pydatetime()
        except Exception:
            return None
    if isinstance(obj, (int, float)):
        try:
            return datetime.fromtimestamp(obj)
        except Exception:
            return None
    return obj

# fetch normalized records (works for ORM or dict)
def fetch_records(record_type):
    rows = []
    try:
        if session and HealthRecord is not None:
            recs = session.query(HealthRecord).filter(HealthRecord.user_id == (user['id'] if isinstance(user, dict) else user.id), HealthRecord.recorded_at >= seven_days_ago, HealthRecord.type == record_type).order_by(HealthRecord.recorded_at.asc()).all()
            for r in recs:
                rows.append({"type": getattr(r, "type", None), "value": getattr(r, "value", None), "notes": getattr(r, "notes", None), "ts": getattr(r, "recorded_at", None)})
        elif agent and hasattr(agent, "list_health_records"):
            recs = agent.list_health_records(user['id'] if isinstance(user, dict) else user.id, record_type=record_type, limit=500)
            for r in recs:
                rows.append({"type": r.get("type"), "value": r.get("value"), "notes": r.get("notes"), "ts": r.get("recorded_at") or r.get("record_date") or r.get("date")})
        elif db_module and hasattr(db_module, "list_health_records"):
            recs = db_module.list_health_records(user['id'] if isinstance(user, dict) else user.id, record_type=record_type, limit=500)
            for r in recs:
                rows.append({"type": r.get("type"), "value": r.get("value"), "notes": r.get("notes"), "ts": r.get("recorded_at")})
    except Exception:
        pass
    return rows

bp_records = fetch_records("bp")
sugar_records = fetch_records("sugar")

# steps
def fetch_steps():
    rows = []
    try:
        if agent and hasattr(agent, "list_fitness_records"):
            recs = agent.list_fitness_records(user['id'] if isinstance(user, dict) else user.id, limit=500)
            for r in recs:
                rows.append({"steps": r.get("steps") if isinstance(r, dict) else getattr(r, "steps", None), "ts": r.get("record_date") or r.get("date") or getattr(r, "date", None)})
        elif db_module and hasattr(db_module, "list_fitness_records"):
            recs = db_module.list_fitness_records(user_id=(user['id'] if isinstance(user, dict) else user.id), limit=500)
            for r in recs:
                rows.append({"steps": r.get("steps"), "ts": r.get("record_date")})
        elif session and FitnessRecord is not None:
            recs = session.query(FitnessRecord).filter(FitnessRecord.user_id == (user['id'] if isinstance(user, dict) else user.id), FitnessRecord.date >= seven_days_ago).order_by(FitnessRecord.date.asc()).all()
            for r in recs:
                rows.append({"steps": getattr(r, "steps", None), "ts": getattr(r, "date", None)})
    except Exception:
        pass
    return rows

steps_records = fetch_steps()

# Normalize and build dataframes
def normalize_bp(records):
    data = []
    for r in records:
        ts = to_dt(r.get("ts"))
        s, d = extract_bp(r.get("value"))
        if s is not None and d is not None and ts is not None:
            data.append({"ts": ts, "systolic": s, "diastolic": d})
    return pd.DataFrame(data)

def normalize_sugar(records):
    data = []
    for r in records:
        ts = to_dt(r.get("ts"))
        v = extract_number(r.get("value"))
        if v is not None and ts is not None:
            data.append({"ts": ts, "sugar": v})
    return pd.DataFrame(data)

def normalize_steps(records):
    data = []
    for r in records:
        ts = to_dt(r.get("ts"))
        steps = extract_number(r.get("steps"))
        if steps is not None and ts is not None:
            data.append({"ts": ts, "steps": int(steps)})
    return pd.DataFrame(data)

df_bp = normalize_bp(bp_records)
df_sugar = normalize_sugar(sugar_records)
df_steps = normalize_steps(steps_records)

def safe_mean(series):
    try:
        return float(series.mean())
    except Exception:
        return None

systolic_avg = safe_mean(df_bp["systolic"]) if not df_bp.empty else None
diastolic_avg = safe_mean(df_bp["diastolic"]) if not df_bp.empty else None
sugar_avg = safe_mean(df_sugar["sugar"]) if not df_sugar.empty else None
steps_avg = int(safe_mean(df_steps["steps"])) if (not df_steps.empty and not math.isnan(safe_mean(df_steps["steps"]))) else None

# Flags
bp_emergency = False
bp_high_count = 0
if not df_bp.empty:
    bp_emergency = ((df_bp["systolic"] >= 180) | (df_bp["diastolic"] >= 120)).any()
    bp_high_count = int(((df_bp["systolic"] >= 140) | (df_bp["diastolic"] >= 90)).sum())

sugar_very_high = False
sugar_low = False
if not df_sugar.empty:
    sugar_very_high = (df_sugar["sugar"] >= 300).any() or (df_sugar["sugar"] >= 180).any()
    sugar_low = (df_sugar["sugar"] <= 70).any()

# Render metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Avg systolic (7d)", f"{int(systolic_avg)}" if systolic_avg is not None else "—")
c2.metric("Avg diastolic (7d)", f"{int(diastolic_avg)}" if diastolic_avg is not None else "—")
c3.metric("Avg sugar (7d)", f"{int(sugar_avg)}" if sugar_avg is not None else "—")
c4.metric("Avg steps (7d)", f"{steps_avg}" if steps_avg is not None else "—")

if bp_emergency:
    st.error("⚠ Emergency BP detected in last 7 days. Advise immediate attention.")
elif bp_high_count > 0:
    st.warning(f"⚠ {bp_high_count} high BP reading(s) in the last 7 days.")
if sugar_very_high:
    st.warning("⚠ One or more very high sugar readings detected.")
if sugar_low:
    st.warning("⚠ One or more low sugar readings detected.")

# Charts
try:
    if not df_bp.empty:
        df_bp2 = df_bp.set_index("ts").sort_index()
        st.line_chart(df_bp2[["systolic", "diastolic"]], height=220)
    if not df_sugar.empty:
        df_sugar2 = df_sugar.set_index("ts").sort_index()
        st.line_chart(df_sugar2["sugar"], height=180)
    if not df_steps.empty:
        df_steps2 = df_steps.set_index("ts").sort_index()
        st.line_chart(df_steps2["steps"], height=180)
except Exception:
    st.write("Charts unavailable (pandas required or data parsing issue).")

<<<<<<< HEAD


# ---------------- Health Report Generation ----------------
st.markdown("---")
st.subheader("🧾 Generate Health Report")

# Date range picker (default last 7 days)
from datetime import timedelta as _timedelta

today_local = datetime.now(timezone.utc).astimezone(IST).date()
default_from = (datetime.now(timezone.utc) - _timedelta(days=7)).date()

with st.form("report_form"):
    r_from = st.date_input("From", value=default_from, key="report_from")
    r_to = st.date_input("To", value=today_local, key="report_to")
    include_types = st.multiselect("Include types", options=["bp", "sugar", "fitness"], default=["bp","sugar","fitness"])
    report_title = st.text_input("Report title", value=f"Health report for {user['name'] if isinstance(user, dict) else user.name}")
    gen_btn = st.form_submit_button("Generate report")
    
def _fetch_health_records_between(uid, from_dt_iso, to_dt_iso, types):
    """Return normalized list of health dicts: {'type','value','notes','ts'}"""
    rows = []
    # try agent -> db_module -> session
    try:
        if agent and hasattr(agent, "list_health_records"):
            # agent list supports record_type; fetch for each type
            for t in types:
                rlist = agent.list_health_records(uid, record_type=t, limit=1000) or []
                for r in rlist:
                    rows.append({"type": t, "value": r.get("value"), "notes": r.get("notes"), "ts": r.get("recorded_at") or r.get("record_date") or r.get("date")})
        elif db_module and hasattr(db_module, "list_health_records"):
            for t in types:
                rlist = db_module.list_health_records(uid, record_type=t, limit=1000) or []
                for r in rlist:
                    rows.append({"type": t, "value": r.get("value"), "notes": r.get("notes"), "ts": r.get("recorded_at")})
        elif session and HealthRecord is not None:
            q = session.query(HealthRecord).filter(HealthRecord.user_id == uid, HealthRecord.type.in_(types), HealthRecord.recorded_at >= from_dt_iso, HealthRecord.recorded_at <= to_dt_iso).order_by(HealthRecord.recorded_at.asc()).all()
            for r in q:
                rows.append({"type": getattr(r,"type",None), "value": getattr(r,"value",None), "notes": getattr(r,"notes",None), "ts": getattr(r,"recorded_at",None)})
    except Exception:
        pass
    return rows

def _fetch_fitness_between(uid, from_dt_iso, to_dt_iso):
    rows = []
    try:
        if agent and hasattr(agent, "list_fitness_records"):
            rlist = agent.list_fitness_records(uid, limit=1000) or []
            for r in rlist:
                rows.append({"type":"fitness","steps": r.get("steps"), "calories": r.get("calories"), "notes": r.get("notes"), "ts": r.get("record_date") or r.get("date") or r.get("recorded_at")})
        elif db_module and hasattr(db_module, "list_fitness_records"):
            rlist = db_module.list_fitness_records(user_id=uid, limit=1000) or []
            for r in rlist:
                rows.append({"type":"fitness","steps": r.get("steps"), "calories": r.get("calories"), "notes": r.get("notes"), "ts": r.get("record_date")})
        elif session and FitnessRecord is not None:
            q = session.query(FitnessRecord).filter(FitnessRecord.user_id == uid, FitnessRecord.date >= from_dt_iso, FitnessRecord.date <= to_dt_iso).order_by(FitnessRecord.date.asc()).all()
            for r in q:
                rows.append({"type":"fitness","steps": getattr(r,"steps",None), "calories": getattr(r,"calories",None), "notes": getattr(r,"notes",None), "ts": getattr(r,"date",None)})
    except Exception:
        pass
    return rows

import base64, io
def _img_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, bbox_inches="tight")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    return b64

def _to_iso(dt_obj):
    if dt_obj is None:
        return None
    if isinstance(dt_obj, str):
        return dt_obj
    try:
        return pd.to_datetime(dt_obj).to_pydatetime().isoformat()
    except Exception:
        try:
            return dt_obj.isoformat()
        except Exception:
            return str(dt_obj)

# ---------------- Complete report generation handler (paste replacing incomplete gen_btn block) ----------------
if gen_btn:
    # normalize chosen date range to ISO datetimes (UTC)
    fr_iso = datetime.combine(r_from, time(0, 0)).astimezone(timezone.utc).isoformat()
    to_iso = datetime.combine(r_to, time(23, 59, 59)).astimezone(timezone.utc).isoformat()
    uid = (user['id'] if isinstance(user, dict) else user.id)

    health_rows = []
    fit_rows = []
    try:
        # fetch selected health types
        types_to_fetch = [t for t in include_types if t in ("bp", "sugar")]
        if types_to_fetch:
            health_rows = _fetch_health_records_between(uid, fr_iso, to_iso, types_to_fetch) or []
        if "fitness" in include_types:
            fit_rows = _fetch_fitness_between(uid, fr_iso, to_iso) or []
    except Exception:
        health_rows = health_rows or []
        fit_rows = fit_rows or []

    # build combined dataframe for CSV and report
    records_for_csv = []
    for r in health_rows:
        records_for_csv.append({
            "type": r.get("type"),
            "value": r.get("value"),
            "notes": r.get("notes"),
            "ts": _to_iso(r.get("ts"))
        })
    for r in fit_rows:
        records_for_csv.append({
            "type": "fitness",
            "value": r.get("steps") or "",
            "notes": r.get("notes"),
            "ts": _to_iso(r.get("ts"))
        })

    df_report = pd.DataFrame(records_for_csv)

    if df_report.empty:
        st.warning("No records found for the selected range/types.")
    else:
        # ---------------- Summary lines ----------------
        st.markdown("### Summary")
        summary_lines = []
        try:
            by_type = df_report.groupby("type").size().to_dict()
            for k, v in by_type.items():
                summary_lines.append(f"- {k}: {v} reading(s)")
        except Exception:
            pass

        # bp averages if present
        def _parse_bp_val_safe(s):
            try:
                s2 = str(s).replace(" ", "")
                if "/" in s2:
                    a, b = s2.split("/", 1)
                    sa = int(''.join(ch for ch in a if ch.isdigit())) if any(ch.isdigit() for ch in a) else None
                    sb = int(''.join(ch for ch in b if ch.isdigit())) if any(ch.isdigit() for ch in b) else None
                    return sa, sb
            except Exception:
                pass
            return None, None

        if "bp" in include_types:
            try:
                bp_rows = df_report[df_report["type"] == "bp"]
                syst, dias = [], []
                for v in bp_rows["value"].astype(str):
                    s, d = _parse_bp_val_safe(v)
                    if s is not None:
                        syst.append(s)
                    if d is not None:
                        dias.append(d)
                if syst:
                    summary_lines.append(f"- Avg systolic: {int(pd.Series(syst).mean())}")
                if dias:
                    summary_lines.append(f"- Avg diastolic: {int(pd.Series(dias).mean())}")
            except Exception:
                pass

        # sugar avg
        if "sugar" in include_types:
            try:
                sugar_rows = df_report[df_report["type"] == "sugar"]
                sugar_vals = []
                for v in sugar_rows["value"]:
                    try:
                        sval = ''.join(ch for ch in str(v) if (ch.isdigit() or ch == '.' or ch == '-'))
                        if sval not in ("", ".", "-"):
                            sugar_vals.append(float(sval))
                    except Exception:
                        pass
                if sugar_vals:
                    summary_lines.append(f"- Avg sugar: {int(pd.Series(sugar_vals).mean())}")
            except Exception:
                pass

        # steps avg
        if "fitness" in include_types:
            try:
                fit_rows_df = df_report[df_report["type"] == "fitness"]
                steps_vals = []
                for x in fit_rows_df["value"]:
                    try:
                        s = ''.join(ch for ch in str(x) if (ch.isdigit() or ch == '-'))
                        if s not in ("", "-"):
                            steps_vals.append(int(s))
                    except Exception:
                        pass
                if steps_vals:
                    summary_lines.append(f"- Avg steps: {int(pd.Series(steps_vals).mean())}")
            except Exception:
                pass

        # render summary in streamlit
        for ln in summary_lines:
            st.write(ln)

        # ---------------- Charts (matplotlib -> base64) ----------------
        # ---------- Safe Charts rendering (requires pandas + matplotlib) ----------
        charts_html = ""
        try:
            # ensure pandas present
            import pandas as _pd  # alias local so we don't rely solely on global
            # require matplotlib for images
            import matplotlib.pyplot as plt

            # Build charts only if df_report exists (DataFrame) and not empty
            if isinstance(df_report, _pd.DataFrame) and not df_report.empty:
                # bp chart
                if "bp" in include_types:
                    try:
                        bp_df = df_report[df_report["type"] == "bp"].copy()
                        bp_idx, s_vals, d_vals = [], [], []
                        for _, row in bp_df.iterrows():
                            # reuse your parse function or safe parse here
                            s, d = _parse_bp_val_safe(row["value"])
                            if s is None and d is None:
                                continue
                            ts = _pd.to_datetime(row["ts"], errors="coerce")
                            if _pd.isna(ts):
                                continue
                            bp_idx.append(ts)
                            s_vals.append(s if s is not None else float("nan"))
                            d_vals.append(d if d is not None else float("nan"))
                        if bp_idx:
                            fig, ax = plt.subplots(figsize=(6, 3))
                            ax.plot(bp_idx, s_vals, label="systolic", marker="o")
                            ax.plot(bp_idx, d_vals, label="diastolic", marker="o")
                            ax.legend(); ax.set_title("BP over time")
                            ax.set_xlabel("time"); ax.set_ylabel("mmHg")
                            b64 = _img_to_base64(fig)
                            charts_html += f'<h3>BP chart</h3><img src="data:image/png;base64,{b64}" /><br/>'
                            plt.close(fig)
                    except Exception:
                        # don't crash entire page for one chart
                        charts_html += "<p>BP chart generation failed (data parse issue).</p>"

                # sugar chart
                if "sugar" in include_types:
                    try:
                        sugar_df = df_report[df_report["type"] == "sugar"].copy()
                        sidx, sval = [], []
                        for _, row in sugar_df.iterrows():
                            val = ''.join(ch for ch in str(row["value"]) if (ch.isdigit() or ch == '.' or ch == '-'))
                            if val in ("", ".", "-"):
                                continue
                            ts = _pd.to_datetime(row["ts"], errors="coerce")
                            if _pd.isna(ts):
                                continue
                            sidx.append(ts); sval.append(float(val))
                        if sidx:
                            fig, ax = plt.subplots(figsize=(6, 3))
                            ax.plot(sidx, sval, marker="o")
                            ax.set_title("Sugar over time"); ax.set_xlabel("time"); ax.set_ylabel("value")
                            b64 = _img_to_base64(fig)
                            charts_html += f'<h3>Sugar chart</h3><img src="data:image/png;base64,{b64}" /><br/>'
                            plt.close(fig)
                    except Exception:
                        charts_html += "<p>Sugar chart generation failed (data parse issue).</p>"

                # steps chart
                if "fitness" in include_types:
                    try:
                        fit_df = df_report[df_report["type"] == "fitness"].copy()
                        fidx, fval = [], []
                        for _, row in fit_df.iterrows():
                            sval = ''.join(ch for ch in str(row["value"]) if (ch.isdigit() or ch == '-'))
                            if sval in ("", "-"):
                                continue
                            ts = _pd.to_datetime(row["ts"], errors="coerce")
                            if _pd.isna(ts):
                                continue
                            fidx.append(ts); fval.append(int(sval))
                        if fidx:
                            fig, ax = plt.subplots(figsize=(6, 3))
                            ax.plot(fidx, fval, marker="o")
                            ax.set_title("Steps over time"); ax.set_xlabel("time"); ax.set_ylabel("steps")
                            b64 = _img_to_base64(fig)
                            charts_html += f'<h3>Steps chart</h3><img src="data:image/png;base64,{b64}" /><br/>'
                            plt.close(fig)
                    except Exception:
                        charts_html += "<p>Steps chart generation failed (data parse issue).</p>"

            else:
                charts_html = "<p>No data for charts (empty dataset).</p>"

        except ImportError as ie:
            # pandas or matplotlib missing
            charts_html = "<p>Charts unavailable: please install <code>pandas</code> and <code>matplotlib</code> in your venv.</p>"
        except Exception as e:
            charts_html = f"<p>Charts unavailable (unexpected error): {str(e)}</p>"

        # display charts_html in report preview
        if charts_html:
            try:
                st.markdown(charts_html, unsafe_allow_html=True)
            except Exception:
                st.write("Charts preview not available; use Download HTML to see visual report.")

        # ---------------- Build HTML report ----------------
        html_parts = []
        html_parts.append("""<html><head><meta charset='utf-8'><title>{}</title>
        <style>
            body {{font-family: Arial, sans-serif; padding: 20px; background: #fafafa;}}
            h1,h2,h3{{color:#2c3e50}}
            .summary-box{{background:#eef5ff;border-left:4px solid #3b7ddd;padding:10px 15px;margin-bottom:15px}}
            table{{width:100%;border-collapse:collapse;margin-top:10px;font-size:14px}}
            th{{background:#4a90e2;color:white;padding:8px}}
            td{{border:1px solid #ccc;padding:8px}}
        </style>
        </head><body>""".format(report_title))

        html_parts.append(f"<h1>{report_title}</h1>")
        html_parts.append(f"<p>User: {user['name'] if isinstance(user, dict) else getattr(user, 'name', uid)}</p>")
        html_parts.append(f"<p>Range: {r_from.isoformat()} → {r_to.isoformat()}</p>")
        html_parts.append("<h2>Summary</h2><div class='summary-box'><ul>")
        for ln in summary_lines:
            html_parts.append(f"<li>{ln}</li>")
        html_parts.append("</ul></div>")

        if charts_html:
            html_parts.append("<h2>Charts</h2>")
            html_parts.append(charts_html)

        # raw records table
        html_parts.append("<h2>Raw records</h2>")
        html_parts.append("<table><thead><tr><th>type</th><th>value</th><th>notes</th><th>ts</th></tr></thead><tbody>")
        for _, row in df_report.sort_values("ts").iterrows():
            ttype = str(row.get("type", ""))
            val = str(row.get("value", ""))
            notes = str(row.get("notes", "") or "")
            ts = str(row.get("ts", "") or "")
            # naive escaping
            html_parts.append(f"<tr><td>{ttype}</td><td>{val}</td><td>{notes}</td><td>{ts}</td></tr>")
        html_parts.append("</tbody></table>")

        html_parts.append("</body></html>")
        html_body = "\n".join(html_parts)

        # ---------------- Present report and downloads in Streamlit ----------------
        st.markdown("### HTML Report (preview)")
        try:
            st.markdown(html_body, unsafe_allow_html=True)
        except Exception:
            st.write("Preview unavailable; use the download button to fetch the report.")

        # Download HTML file
        try:
            st.download_button(
                label="Download HTML report",
                data=html_body,
                file_name=f"health_report_{uid}.html",
                mime="text/html"
            )
        except Exception:
            pass

        # Download CSV of records
        try:
            csv_bytes = df_report.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download CSV of records",
                data=csv_bytes,
                file_name=f"health_report_{uid}.csv",
                mime="text/csv"
            )
        except Exception:
            pass

# --------------------------------------------------------------------------------------------------------------

# ======================== DAY 4 — Data Import / Export ========================
st.markdown("---")
st.subheader("📂 Data Import / Export (JSON / CSV / XML)")


# ------------------------- IMPORT JSON -------------------------
st.markdown("### 📥 Import from JSON")
json_file = st.file_uploader("Upload JSON file", type=["json"], key="json_upload")

if json_file is not None:
    import json
    try:
        data = json.load(json_file)
        uid = user['id'] if isinstance(user, dict) else user.id

        imported = 0

        # JSON can contain: bp, sugar, weight, fitness
        if "health_records" in data:
            for rec in data["health_records"]:
                typ = rec.get("type")
                val = rec.get("value")
                notes = rec.get("notes")
                if agent and hasattr(agent, "add_health_record"):
                    agent.add_health_record(uid, typ, val, notes)
                else:
                    db_module.add_health_record(uid, typ, val, notes)
                imported += 1

        if "fitness" in data:
            for rec in data["fitness"]:
                steps = rec.get("steps")
                calories = rec.get("calories")
                ts = rec.get("timestamp")
                if agent and hasattr(agent, "add_fitness_record"):
                    agent.add_fitness_record(uid, steps, calories, ts)
                else:
                    db_module.add_fitness_record(uid, steps, calories, ts)
                imported += 1

        st.success(f"Imported {imported} records from JSON!")
        st.rerun()

    except Exception as e:
        st.error(f"JSON import failed: {e}")


# ------------------------- IMPORT XML -------------------------
st.markdown("### 📥 Import from XML")
xml_file = st.file_uploader("Upload XML file", type=["xml"], key="xml_upload")

if xml_file is not None:
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_file)
        root = tree.getroot()
        uid = user['id'] if isinstance(user, dict) else user.id
        imported = 0

        # <health><record type="bp" value="120/80" notes="..." /></health>
        for rec in root.findall(".//record"):
            typ = rec.attrib.get("type")
            val = rec.attrib.get("value")
            notes = rec.attrib.get("notes")
            if agent:
                agent.add_health_record(uid, typ, val, notes)
            else:
                db_module.add_health_record(uid, typ, val, notes)
            imported += 1

        # <fitness steps="" calories="" timestamp="" />
        for rec in root.findall(".//fitness"):
            steps = rec.attrib.get("steps")
            cal = rec.attrib.get("calories")
            ts = rec.attrib.get("timestamp")
            if agent:
                agent.add_fitness_record(uid, steps, cal, ts)
            else:
                db_module.add_fitness_record(uid, steps, cal, ts)
            imported += 1

        st.success(f"Imported {imported} records from XML!")
        st.rerun()

    except Exception as e:
        st.error(f"XML import failed: {e}")


# ------------------------- EXPORT: JSON / CSV / XML -------------------------
st.markdown("### 📤 Export All User Health Data")

uid = user['id'] if isinstance(user, dict) else user.id

# Get data
all_health = db_module.list_health_records(uid, limit=9999)
all_fitness = db_module.list_fitness_records(uid, limit=9999)
all_meds = db_module.list_medications(uid)

export_data = {
    "user_id": uid,
    "health_records": all_health,
    "fitness_records": all_fitness,
    "medications": all_meds
}

# ---- JSON export ----
json_bytes = json.dumps(export_data, indent=2).encode("utf-8")
st.download_button("📥 Download JSON", json_bytes, "health_export.json", "application/json")

# ---- CSV export (health only) ----
import pandas as pd
try:
    df_csv = pd.DataFrame(all_health)
    csv_bytes = df_csv.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV (health)", csv_bytes, "health_export.csv", "text/csv")
except:
    st.warning("Could not generate CSV — no health records.")

# ---- XML export ----
def to_xml(data):
    import xml.etree.ElementTree as ET
    root = ET.Element("HealthData")

    health_el = ET.SubElement(root, "HealthRecords")
    for r in data["health_records"]:
        rec = ET.SubElement(health_el, "Record")
        for k, v in r.items():
            rec.set(k, str(v))

    fit_el = ET.SubElement(root, "FitnessRecords")
    for r in data["fitness_records"]:
        rec = ET.SubElement(fit_el, "Fitness")
        for k, v in r.items():
            rec.set(k, str(v))

    meds_el = ET.SubElement(root, "Medications")
    for r in data["medications"]:
        rec = ET.SubElement(meds_el, "Medication")
        for k, v in r.items():
            rec.set(k, str(v))

    return ET.tostring(root, encoding="utf-8")

xml_bytes = to_xml(export_data)
st.download_button("📥 Download XML", xml_bytes, "health_export.xml", "application/xml")



=======
>>>>>>> 6d768788236e5406ac5ab5cf55c6a3d4fcc57964
# ---------------- Reminders (place this after the Medication List block) ----------------
st.markdown("---")
st.subheader("⏰ Reminders")

# Gather medications for the current user (works with agent, db_module, or SQLAlchemy)
try:
    if agent and hasattr(agent, "list_medications"):
        meds_all = agent.list_medications(user['id'] if isinstance(user, dict) else user.id)
    elif db_module and hasattr(db_module, "list_medications"):
        meds_all = db_module.list_medications(user_id=(user['id'] if isinstance(user, dict) else user.id))
    elif session and Medication is not None:
        meds_all = session.query(Medication).filter_by(user_id=(user['id'] if isinstance(user, dict) else user.id)).all()
    else:
        meds_all = []
except Exception:
    meds_all = []

now = datetime.now(timezone.utc).astimezone(IST)  # local IST now
reminders = []

# meds_all may be list of dicts (db.py/agent) or ORM objects
for m in meds_all:
    try:
        # get time string (support 'times' key (csv style) and 'time' field from ORM)
        time_str = m.get("times") if isinstance(m, dict) else getattr(m, "time", None)
        name = m.get("name") if isinstance(m, dict) else getattr(m, "name", "Medication")
        dose = m.get("dose") if isinstance(m, dict) else getattr(m, "dose", "")
        # times might be comma-separated — take each
        if not time_str:
            continue
        times_list = [t.strip() for t in str(time_str).split(",") if t.strip()]
        for t in times_list:
            mins = minutes_until(t)
            if mins is None:
                continue
            # only show meds within -60 .. +180 min window (adjust as you like)
            if -60 <= mins <= 180:
                status = "TAKE NOW" if mins <= 0 else f"In {mins} min"
                reminders.append({"mins": mins, "name": name, "dose": dose, "time": t, "status": status})
    except Exception:
        continue

if not reminders:
    st.info("No immediate reminders.")
else:
    # sort by soonest (most negative first)
    reminders.sort(key=lambda x: x["mins"])
    for r in reminders:
        if r["status"] == "TAKE NOW":
            st.warning(f"⚠ TAKE NOW — {r['name']} ({r['dose'] or 'no dose specified'}) scheduled at {r['time']}")
        else:
            st.write(f"🔔 {r['name']} — {r['dose'] or ''} at {r['time']} — {r['status']}")

# optional: Add simple action buttons to mark a med as taken (local state)
if reminders:
    with st.expander("Mark a reminder as taken"):
        name_to_mark = st.selectbox("Pick medication", [r["name"] + " @ " + r["time"] for r in reminders], key="mark_med_select")
        if st.button("Mark taken"):
            st.success(f"Marked {name_to_mark} as taken .")
<<<<<<< HEAD
# ---------------- Natural Language Query Section ----------------
st.markdown("---")
st.subheader("💬 Ask Health Questions")

from nlp_utils import interpret_query
from health_query_engine import answer_parsed_query

user_question = st.text_input(
    "Ask something (e.g., 'What is my latest BP?', 'How many steps last week?')"
)

if user_question:
    uid = user['id'] if isinstance(user, dict) else user.id
    parsed = interpret_query(user_question)

    #st.caption(f"Parsed query: {parsed}")

    response = answer_parsed_query(parsed, user_id=uid)

    st.success(response)
=======
>>>>>>> 6d768788236e5406ac5ab5cf55c6a3d4fcc57964



# ---------------- Chatbot / Assistant (light) ----------------
st.markdown("---")
st.subheader("💬 Chatbot Assistant (text commands)")

# safe_rerun helper
try:
    safe_rerun
except NameError:
    def safe_rerun():
        try:
            st.rerun()
        except Exception:
            st.markdown("<script>window.location.reload()</script>", unsafe_allow_html=True)

# import chatbot handler if exists
try:
    from chatbot import handle_query
    chatbot_available = True
except Exception:
    handle_query = None
    chatbot_available = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

query = st.text_input("Ask the assistant (try 'help')", key="chat_in")
send = st.button("Send")

if send and query and query.strip():
    try:
        if chatbot_available:
            answer = handle_query(user['id'] if isinstance(user, dict) else user.id, query)
        else:
            answer = "Chatbot not available in this environment."
    except Exception as e:
        answer = f"Error: {e}"
    st.session_state.chat_history.append(("You: " + query, "Bot: " + answer))
    safe_rerun()

for user_msg, bot_msg in st.session_state.chat_history[::-1]:
    st.write(user_msg)
    st.write(bot_msg)