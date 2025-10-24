
# seed_data.py
from models import init_db, get_engine_and_session, User, Medication, HealthRecord

# Initialize DB (creates tables if not exist)
init_db()
engine, SessionLocal = get_engine_and_session()
session = SessionLocal()

# Check if there is already at least one user
if not session.query(User).first():
    # Create a sample user
    u = User(name="Test User", dob="1990-01-01", phone="9999999999")
    session.add(u)
    session.commit()

    # Add sample medications
    meds = [
        Medication(user_id=u.id, name="Aspirin", dose="75 mg", time="08:00", frequency="Daily"),
        Medication(user_id=u.id, name="Vitamin D", dose="1 tab", time="20:00", frequency="Daily"),
    ]
    session.add_all(meds)
    session.commit()

    # Add sample health records
    records = [
        HealthRecord(user_id=u.id, type="bp", value="120/78"),
        HealthRecord(user_id=u.id, type="sugar", value="110"),
    ]
    session.add_all(records)
    session.commit()

    print("✅ Database seeded successfully!")
else:
    print("ℹ️ Database already has data.")
