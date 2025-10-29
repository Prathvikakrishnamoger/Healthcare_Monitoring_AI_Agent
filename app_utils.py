# app_utils.py
import re

def parse_bp(value: str) -> str:
    """
    Parse BP string like "120/80" and return a human-friendly classification.
    Returns short text like "Normal", "Elevated", "High blood pressure (Stage 1)", etc.
    """
    if not value:
        return "No BP value"
    # accept strings like "120/80" or "120 / 80"
    m = re.match(r"\s*(\d{2,3})\s*/\s*(\d{2,3})\s*$", str(value))
    if not m:
        return "Invalid BP format"
    try:
        sys = int(m.group(1))
        dia = int(m.group(2))
    except ValueError:
        return "Invalid BP numbers"

    # classification following simplified AHA-style ranges
    if sys >= 180 or dia >= 120:
        return "Hypertensive crisis — emergency"
    if sys >= 140 or dia >= 90:
        return "High blood pressure (Stage 2)"
    if 130 <= sys < 140 or 80 <= dia < 90:
        return "High blood pressure (Stage 1)"
    if 120 <= sys < 130 and dia < 80:
        return "Elevated blood pressure"
    if sys < 120 and dia < 80:
        return "Normal blood pressure"
    return "BP value unusual"

def parse_sugar(value: str) -> str:
    """
    Parse a sugar/glucose value (fasting mg/dL or numeric) and return a short classification.
    This is a simple numeric parser - adapt thresholds as needed.
    """
    if value is None:
        return "No sugar value"
    # strip any non-digit except dot
    s = str(value).strip()
    m = re.search(r"(\d+(\.\d+)?)", s)
    if not m:
        return "Invalid sugar value"
    try:
        val = float(m.group(1))
    except ValueError:
        return "Invalid sugar number"

    # thresholds in mg/dL (very simple):
    if val >= 300:
        return "Very high — emergency"
    if val >= 200:
        return "High — likely hyperglycemia"
    if val >= 140:
        return "Elevated (postprandial/OGTT range)"
    if 70 <= val < 100:
        return "Normal range"
    if val < 70:
        return "Low blood sugar (hypoglycemia)"
    return "Sugar level note"