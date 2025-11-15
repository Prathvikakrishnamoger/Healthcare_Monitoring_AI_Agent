# app.py 

import streamlit as st
import re
import os
import math
import pandas as pd

from datetime import datetime, date, time, timezone, timedelta

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
        tstr = time_input.strftime("%H:%M")
        if not mname.strip():
            st.error("Medication name is required.")
        elif not validate_dose(dose.strip()):
            st.error("Dose looks invalid (too long).")
        elif not validate_time_str(tstr):
            st.error("Time must be in HH:MM format.")
        else:
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
        else:
            st.error("Please enter a value.")

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
    records = []

if not records:
    st.info("No health records yet.")
else:
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