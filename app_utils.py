# app_utils.py
def parse_bp(value: str) -> str:
    """Parse systolic/diastolic and return classification."""
    try:
        parts = value.split("/")
        if len(parts) != 2:
            return "Invalid BP"
        sys = int(parts[0])
        dia = int(parts[1])
    except Exception:
        return "Invalid BP"

    if sys >= 180 or dia >= 120:
        return "Hypertensive crisis — seek immediate help"
    if sys >= 140 or dia >= 90:
        return "High blood pressure (Stage 2)"
    if sys >= 130 or dia >= 80:
        return "Elevated / Stage 1"
    return "Normal"


def parse_sugar(value: str) -> str:
    """Parse numeric sugar value (mg/dL) and return classification."""
    try:
        v = float(value)
    except Exception:
        return "Invalid sugar"

    if v >= 300:
        return "Very high (medical attention needed)"
    if v >= 200:
        return "High — emergency range"
    if v >= 140:
        return "High / borderline"
    if v >= 70:
        return "Normal"
    return "Low (hypoglycemia) — take action"