# chatbot.py
"""
Simple rule-based chatbot that reads/writes to the project's SQLite DB via models.py.
Supported commands (case-insensitive):
 - show meds
 - next med
 - add med NAME;DOSE;HH:MM
 - latest bp
 - help
"""

from models import get_engine_and_session, Medication, HealthRecord
import datetime

engine, SessionLocal = get_engine_and_session()
session = SessionLocal()


def handle_query(user_id, text):
    text = (text or "").strip()
    if not text:
        return "Please type a command (try 'help')."

    lower = text.lower()

    # HELP
    if "help" in lower:
        return (
            "Commands:\n"
            "- show meds → list medications\n"
            "- next med → next medication scheduled\n"
            "- add med NAME;DOSE;HH:MM → add medication\n"
            "- latest bp → show last blood pressure record"
        )

    # SHOW MEDS
    if "show meds" in lower or "list meds" in lower:
        meds = session.query(Medication).filter_by(user_id=user_id).order_by(Medication.times).all()
        if not meds:
            return "No medications found."
        lines = []
        for m in meds:
            lines.append(f"{m.name} — {m.dose or ''} at {m.times}")
        return "\n".join(lines)

    # NEXT MED
    if "next med" in lower or "next medication" in lower:
        meds = session.query(Medication).filter_by(user_id=user_id).all()
        if not meds:
            return "No medications listed."
        now = datetime.datetime.now()
        upcoming = []
        for m in meds:
            try:
                med_time = datetime.datetime.strptime(m.times, "%H:%M").time()
                med_dt = datetime.datetime.combine(now.date(), med_time)
                delta_min = int((med_dt - now).total_seconds() / 60)
                upcoming.append((delta_min, m))
            except Exception:
                continue
        if not upcoming:
            return "No valid medication times found."
        # sort by nearest future (prefer soonest)
        upcoming.sort(key=lambda x: (x[0] < 0, abs(x[0])))
        next_med = upcoming[0][1]
        return f"Next medication: {next_med.name} — {next_med.dose or ''} at {next_med.times}"

    # ADD MED via text
    if lower.startswith("add med "):
        payload = text[len("add med "):]
        parts = [p.strip() for p in payload.split(";")]
        if len(parts) != 3:
            return "Invalid format. Use: add med NAME;DOSE;HH:MM"
        name, dose, t = parts
        # validate time
        try:
            datetime.datetime.strptime(t, "%H:%M")
        except Exception:
            return "Invalid time format. Use HH:MM (24h)."
        try:
            med = Medication(user_id=user_id, name=name.title(), dose=dose, time=t, frequency="Daily")
            session.add(med)
            session.commit()
            return f"Added medication: {med.name} at {med.times}"
        except Exception as e:
            session.rollback()
            return f"Error saving medication: {e}"

    # LATEST BP
    if "latest bp" in lower or lower == "bp":
        rec = (
            session.query(HealthRecord)
            .filter_by(user_id=user_id, type="bp")
            .order_by(HealthRecord.recorded_at.desc())
            .first()
        )
        if rec:
            return f"Latest BP: {rec.value} (recorded {rec.recorded_at.strftime('%Y-%m-%d %H:%M')})"
        return "No BP records found."

    # Default
    return "Sorry, I didn't understand. Type 'help' for a list of commands."