# app.py
import streamlit as st
import datetime
from models import init_db, get_engine_and_session, User, Medication, HealthRecord

# Initialize database
init_db()
engine, SessionLocal = get_engine_and_session()
session = SessionLocal()

st.set_page_config(page_title="Healthcare Monitoring AI Agent", layout="centered")
st.title("💊 Healthcare Monitoring AI Agent — Week 2 Day 2")

# Sidebar: user management
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
        if mname.strip():
            med = Medication(
                user_id=user.id,
                name=mname.strip(),
                dose=dose.strip(),
                time=time_input.strftime("%H:%M"),
                frequency=freq,
                notes=notes.strip()
            )
            session.add(med)
            session.commit()
            st.success(f"✅ Added {mname}")
            st.rerun()
        else:
            st.error("Please enter a medication name.")

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

# Display recent records
st.subheader("Recent Health Records 🧾")
recs = session.query(HealthRecord).filter_by(user_id=user.id).order_by(HealthRecord.recorded_at.desc()).limit(10).all()
if recs:
    for r in recs:
        st.write(f"- {r.type.upper()} | {r.value} | {r.recorded_at.strftime('%Y-%m-%d %H:%M')}")
else:
    st.info("No health records yet.")
# ---------------------- CHATBOT SECTION ----------------------
st.markdown("---")
st.subheader("💬 Chatbot Assistant (text commands)")

# helper to safely rerun across Streamlit versions (optional)
def safe_rerun():
    try:
        st.experimental_rerun()
    except Exception:
        st.markdown("<script>window.location.reload()</script>", unsafe_allow_html=True)

from chatbot import handle_query

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

query = st.text_input("Ask the assistant (try 'help')", key="chat_in")
send = st.button("Send")

if send and query.strip():
    answer = handle_query(user.id, query)
    st.session_state.chat_history.append(("You: " + query, "Bot: " + answer))
    # try to refresh view so new med appears in lists
    safe_rerun()

# show history (most recent first)
for user_msg, bot_msg in st.session_state.chat_history[::-1]:
    st.write(user_msg)
    st.write(bot_msg)


