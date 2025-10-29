# app.py
import streamlit as st
import datetime
from models import init_db, get_engine_and_session, User, Medication, HealthRecord

# --------- Helpers: validation & time parsing ---------
import re
import datetime as _dt

def validate_time_str(tstr):
    """Return True if 'HH:MM' 24h format."""
    return bool(re.match(r'^[0-2]?\d:[0-5]\d$', tstr))

def validate_dose(dose):
    """Basic dose validation: not empty and reasonable length."""
    if not dose: 
        return True   # dose can be empty (optional), allow it
    return 1 <= len(dose) <= 60

def minutes_until(time_hhmm):
    """Return minutes from now until the given HH:MM (int). Can be negative."""
    now = _dt.datetime.now()
    try:
        t = _dt.datetime.strptime(time_hhmm, "%H:%M").time()
    except Exception:
        return None
    med_dt = _dt.datetime.combine(now.date(), t)
    return int((med_dt - now).total_seconds() // 60)


# ------------------------ Initialize database ------------------------
from models import init_db, get_engine_and_session, User, Medication, HealthRecord
import os
import datetime as _dt

# Step 1: Create tables if not exist
init_db()

# Step 2: Get DB engine and session
engine, SessionLocal = get_engine_and_session()
session = SessionLocal()

# ------------------------ Step 3: Auto-seed default user & sample data (only first time) ------------------------
from seed_data import seed_default_data
import datetime as dt

def initialize_default_data():
    """Automatically create default user and sample records if DB empty."""
    engine, SessionLocal = get_engine_and_session()
    s = SessionLocal()
    try:
        # Check if user table is empty
        if s.query(User).count() == 0:
            print("Seeding default user with example medication and health record...")
            # Create default user
            default_user = User(
                name="Test User",
                dob="1990-01-01",
                phone="9999999999",
                notes="Auto-seeded user"
            )
            s.add(default_user)
            s.commit()

            # Add sample medications
            meds = [
                Medication(
                    user_id=default_user.id,
                    name="Aspirin",
                    dose="75 mg",
                    time="08:00",
                    frequency="Daily",
                    notes="Auto-seeded medication"
                ),
                Medication(
                    user_id=default_user.id,
                    name="Vitamin D",
                    dose="1 tab",
                    time="20:00",
                    frequency="Daily",
                    notes="Auto-seeded medication"
                ),
            ]
            s.add_all(meds)
            s.commit()

            # Add sample health records
            records = [
                HealthRecord(
                    user_id=default_user.id,
                    type="bp",
                    value="120/78",
                    recorded_at=dt.datetime.now(),
                    notes="Auto-seeded BP record"
                ),
                HealthRecord(
                    user_id=default_user.id,
                    type="sugar",
                    value="110",
                    recorded_at=dt.datetime.now(),
                    notes="Auto-seeded sugar record"
                ),
            ]
            s.add_all(records)
            s.commit()

            print("✅ Database initialized and sample data added.")
        else:
            print("ℹ Database already has data.")
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        s.rollback()
    finally:
        s.close()

# Run safe seeding logic (once)
initialize_default_data()
#------------------------------
# Step 4: Run seeding logic if no DB file or user data exists
db_path = os.getenv("DB_PATH", "sqlite:///meds.db")
if db_path.startswith("sqlite:///"):
    local_db_file = db_path.replace("sqlite:///", "")
    if not os.path.exists(local_db_file):
        print("ℹ Creating new database file and seeding default data...")
        seed_default_data()
    else:
        # Check if user table empty (for safety)
        if session.query(User).count() == 0:
            print("ℹ Database exists but no users found — seeding default data...")
            seed_default_data()
else:
    # For non-sqlite databases, just ensure at least one user exists
    if session.query(User).count() == 0:
        seed_default_data()

# ------------------------ Streamlit Page Setup ------------------------
import streamlit as st
st.set_page_config(page_title="Healthcare Monitoring AI Agent", layout="centered")
st.title("💊 Healthcare Monitoring AI Agent")




#----------------- Sidebar: user management
st.sidebar.header("Select or Add User")
users = session.query(User).all()
user_choice = st.sidebar.selectbox("Select User", [u.name for u in users] if users else ["No users found"])

with st.sidebar.expander("➕ Add New User"):
    with st.form("add_user"):
        name = st.text_input("Full Name")
        dob = st.text_input("DOB (YYYY-MM-DD)")
        phone = st.text_input("Phone")
        add_user = st.form_submit_button("Add User")
        if add_user:
            if name.strip():
                u = User(name=name.strip(), dob=dob.strip(), phone=phone.strip())
                session.add(u)
                session.commit()
                st.success("✅ User added successfully! Reload page.")
                st.rerun()
            else:
                st.error("Please enter a name.")

# Stop app if no users
if not users:
    st.info("Please add a user from the sidebar to continue.")
    st.stop()

user = session.query(User).filter_by(name=user_choice).first()
st.header(f"Welcome, {user.name}")
#--------------alert code---------
from app_utils import parse_bp, parse_sugar
recent_critical = []
now = _dt.datetime.now()
day_ago = now - _dt.timedelta(hours=24)
recs_24 = session.query(HealthRecord).filter(HealthRecord.user_id==user.id, HealthRecord.recorded_at >= day_ago).all()
for r in recs_24:
    if r.type == "bp":
        if "crisis" in parse_bp(r.value).lower() or "emergency" in parse_bp(r.value).lower():
            recent_critical.append((r, parse_bp(r.value)))
    if r.type == "sugar":
        if "emergency" in parse_sugar(r.value).lower() or "very high" in parse_sugar(r.value).lower() or "low" in parse_sugar(r.value).lower():
            recent_critical.append((r, parse_sugar(r.value)))

if recent_critical:
    st.markdown("---")
    st.error("🚨 Recent critical readings detected. Check the Recent Health Records section for details.")


# Add medication form
st.subheader("Add Medication 💊")
with st.form("add_med_form"):
    mname = st.text_input("Medication Name")
    dose = st.text_input("Dose (e.g., 1 tab, 75 mg)")
    time_input = st.time_input("Time to take", value=datetime.time(8, 0))
    freq = st.selectbox("Frequency", ["Daily", "Once", "Alternate Days"])
    notes = st.text_area("Notes (optional)")
    submit_med = st.form_submit_button("Add Medication")
    if submit_med:
        # build time string
        tstr = time_input.strftime("%H:%M")

        # validations
        if not mname.strip():
            st.error("Medication name is required.")
        elif not validate_dose(dose.strip()):
            st.error("Dose looks invalid (too long).")
        elif not validate_time_str(tstr):
            st.error("Time must be in HH:MM format.")
        else:
            med = Medication(
                user_id=user.id,
                name=mname.strip(),
                dose=dose.strip(),
                time=tstr,
                frequency=freq,
                notes=notes.strip()
            )
            session.add(med)
            session.commit()
            st.success(f"✅ Added {med.name} at {med.time}")
            safe_rerun()


# Show medication list
st.subheader("📋 Medication List")
meds = session.query(Medication).filter_by(user_id=user.id).all()
if meds:
    for m in meds:
        c1, c2 = st.columns([6, 1])
        c1.write(f"**{m.name}** — {m.dose or ''} at {m.time} ({m.frequency})")
        if c2.button("🗑️", key=f"del-{m.id}"):
            session.delete(m)
            session.commit()
            st.warning(f"Deleted {m.name}")
            st.rerun()
else:
    st.info("No medications found.")

# Add health record
st.subheader("Add Health Record 🩺")
with st.form("add_health_form"):
    htype = st.selectbox("Type", ["bp", "sugar", "weight"])
    hvalue = st.text_input("Value (e.g., BP: 120/80  |  Sugar: 110)")
    hnotes = st.text_area("Notes")
    add_health = st.form_submit_button("Add Record")
    if add_health:
        if hvalue.strip():
            rec = HealthRecord(user_id=user.id, type=htype, value=hvalue.strip(), notes=hnotes.strip())
            session.add(rec)
            session.commit()
            st.success("✅ Health record added!")
            st.rerun()
        else:
            st.error("Please enter a value.")

# ---------------- Show recent health records ----------------
st.subheader("Recent Health Records 🧾")

# import parsers (make sure app_utils.py is in same folder)
from app_utils import parse_bp, parse_sugar

records = session.query(HealthRecord).filter_by(user_id=user.id).order_by(HealthRecord.recorded_at.desc()).limit(20).all()
if not records:
    st.info("No health records yet.")
else:
    # show newest first
    for r in records:
        ts = r.recorded_at.strftime('%Y-%m-%d %H:%M')
        note = f" — {r.notes}" if r.notes else ""
        extra = ""
        alert = None

        # classify reading
        if r.type == "bp":
            extra = parse_bp(r.value)
            # flag critical BP readings
            if "crisis" in extra.lower() or "emergency" in extra.lower():
                alert = f"⚠ {extra}"
        elif r.type == "sugar":
            extra = parse_sugar(r.value)
            # flag critical sugar readings
            if "emergency" in extra.lower() or "very high" in extra.lower() or "low" in extra.lower():
                alert = f"⚠ {extra}"
        elif r.type == "weight":
            extra = f"{r.value}"

        display = f"- *{r.type.upper()}* | {r.value} | {extra} | {ts}{note}"

        # style output
        if alert:
            st.warning(display)
            st.error(alert)
        else:
            st.write(display)
     
# ---------------- Reminders (show nearby meds) ----------------
st.markdown("---")
st.subheader("⏰ Reminders")

now = _dt.datetime.now()
meds_all = session.query(Medication).filter_by(user_id=user.id).all()
reminders = []
for m in meds_all:
    mins = minutes_until(m.time)
    if mins is None:
        continue
    # show meds within -60 .. +180 minutes window
    if -60 <= mins <= 180:
        status = "TAKE NOW" if mins <= 0 else f"In {mins} min"
        reminders.append((mins, m, status))

if not reminders:
    st.info("No immediate reminders.")
else:
    # sort by soonest (most negative first means already due; we want those first)
    reminders.sort(key=lambda x: x[0])
    for mins, m, status in reminders:
        if status == "TAKE NOW":
            st.warning(f"⚠️ TAKE NOW — {m.name} ({m.dose or 'no dose specified'}) scheduled at {m.time}")
        else:
            st.write(f"🔔 {m.name} — {m.dose or ''} at {m.time} — {status}")

# ---------------------- CHATBOT SECTION ----------------------
st.markdown("---")
st.subheader("💬 Chatbot Assistant (text commands)")


# safe rerun helper (only if not present above)
try:
    safe_rerun
except NameError:
    def safe_rerun():
        try:
            st.rerun()
        except Exception:
            st.markdown("<script>window.location.reload()</script>", unsafe_allow_html=True)

from chatbot import handle_query

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

query = st.text_input("Ask the assistant (try 'help')", key="chat_in")
send = st.button("Send")

if send and query and query.strip():
    answer = handle_query(user.id, query)
    st.session_state.chat_history.append(("You: " + query, "Bot: " + answer))
    safe_rerun()

for user_msg, bot_msg in st.session_state.chat_history[::-1]:
    st.write(user_msg)
    st.write(bot_msg)

