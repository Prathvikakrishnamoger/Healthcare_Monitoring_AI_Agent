# nlp_utils.py
import re
from datetime import datetime, timedelta

def interpret_query(text: str) -> dict:
    if not text:
        return {"intent": "unknown", "time_range": "latest", "date": None, "raw": text}

    t = text.lower().strip()

    # intent detection
    if "blood pressure" in t or "bp" in t:
        intent = "get_bp"
    elif "sugar" in t or "glucose" in t:
        intent = "get_sugar"
    elif "steps" in t or "walk" in t or "step" in t:
        intent = "get_steps"
    elif "goal" in t or "progress" in t:
        intent = "get_goal_status"
    elif "report" in t or "summary" in t:
        intent = "get_report"
    else:
        intent = "unknown"

    # time detection
    date = None
    if "last week" in t or "last 7 days" in t:
        time_range = "last_7_days"
    elif "today" in t:
        time_range = "today"
    elif "yesterday" in t:
        time_range = "yesterday"
    else:
        m = re.search(r'\d{4}-\d{2}-\d{2}', t)
        if m:
            time_range = "specific_date"
            date = m.group(0)
        else:
            time_range = "latest"

    return {
        "intent": intent,
        "time_range": time_range,
        "date": date,
        "raw": text
    }