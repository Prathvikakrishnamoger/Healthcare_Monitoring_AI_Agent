# agent.py
from typing import List, Optional, Dict, Any
import db
from db import get_conn

# ensure DB/tables exist
try:
    db.init_db()
except Exception:
    pass

class HealthAgent:
    """Simple agent wrapper around db.py functions."""

    def __init__(self):
        pass

    # Users
    def list_users(self) -> List[Dict]:
        return db.list_users()

    def add_user(self, name: str, dob: Optional[str] = None, phone: Optional[str] = None) -> int:
        return db.add_user(name, dob, phone)

    # Medications
    def add_medication(self, user_id:int, name:str, dose:str, times:str, frequency:str="Daily", notes:Optional[str]=None) -> Dict[str,Any]:
        mid = db.add_medication(name=name, dose=dose, times=times, user_id=user_id, frequency=frequency, notes=notes)
        return {"id": mid, "user_id": user_id, "name": name, "dose": dose, "times": times, "frequency": frequency, "notes": notes}
    
    # ---------- Medication Taken Events ----------
    def add_med_taken(self, user_id:int, medication_id:int, taken_at:Optional[str]=None, note:Optional[str]=None):
        """Record that a medication was taken."""
        if hasattr(db, "add_med_taken"):
            return db.add_med_taken(user_id, medication_id, taken_at, note)
        raise NotImplementedError("db.add_med_taken not implemented")

    def list_med_taken(self, user_id:int, medication_id:Optional[int]=None, limit:int=100):
        """List recently taken events for a user or a specific medication."""
        if hasattr(db, "list_med_taken"):
            return db.list_med_taken(user_id, medication_id, limit)
        return []

    def list_medications(self, user_id:Optional[int]=None) -> List[Dict]:
        return db.list_medications(user_id)

    def delete_medication(self, med_id:int) -> bool:
        return db.delete_medication(med_id)
    
    def add_alert(self, user_id:int, medication_a:str, medication_b:str, severity:str="moderate", description:Optional[str]=None, note:Optional[str]=None):
        if hasattr(db, "add_alert"):
            return db.add_alert(user_id, medication_a, medication_b, severity, description, note)
        raise NotImplementedError
    def list_alerts(self, user_id:int, limit:int=100):
        if hasattr(db, "list_alerts"):
            return db.list_alerts(user_id, limit)
        return []

    # Health records
    def add_health_record(self, user_id:int, type_:str, value:str, notes:Optional[str]=None) -> Dict[str,Any]:
        rid = db.add_health_record(user_id, type_, value, notes)
        return {"id": rid, "user_id": user_id, "type": type_, "value": value, "notes": notes}

    def list_health_records(self, user_id:int, record_type:Optional[str]=None, limit:int=100) -> List[Dict]:
        return db.list_health_records(user_id, record_type, limit)

    # Fitness
    def add_fitness_record(self, user_id:int, steps:Optional[int]=None, calories:Optional[int]=None, record_date:Optional[str]=None, notes:Optional[str]=None) -> Dict[str,Any]:
        fid = db.add_fitness_record(user_id, steps, calories, record_date, notes)
        return {"id": fid, "user_id": user_id, "steps": steps, "calories": calories, "record_date": record_date, "notes": notes}

    def list_fitness_records(self, user_id:int, limit:int=100) -> List[Dict]:
        return db.list_fitness_records(user_id, limit)
    # ---------- Goals ----------
    # in agent.py (example)
    # agent.py (method inside class)
    def add_goal(self, user_id: int, goal_title: str, goal_type: str,
                target_value=None, unit: str=None, start_date: str=None,
                end_date: str=None, notes: str=None):
        if hasattr(db, "add_goal"):
            return db.add_goal(user_id=user_id,
                            goal_title=goal_title,
                            goal_type=goal_type,
                            target_value=target_value,
                            unit=unit,
                            start_date=start_date,
                            end_date=end_date,
                            notes=notes)
        raise NotImplementedError("db.add_goal not implemented")

    def list_goals(self, user_id: int):
        """Return list of goals as dicts for a user."""
        conn = get_conn()
        c = conn.cursor()
        rows = c.execute("""
            SELECT id, user_id, goal_title, goal_type, target_value, unit, start_date, end_date, notes, created_at
            FROM goals
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_goal(goal_id: int) -> Optional[Dict]:
        conn = get_conn()
        c = conn.cursor()
        row = c.execute("SELECT id, user_id, goal_title, goal_type, target_value, unit, start_date, end_date, notes, created_at FROM goals WHERE id = ?", (goal_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def update_goal(goal_id: int, **kwargs) -> bool:
        """
        Allowed kwargs: title, goal_type, target_value, unit, start_date, end_date, notes
        """
        conn = get_conn()
        c = conn.cursor()
        cur = c.execute("SELECT id, goal_title, goal_type, target_value, unit, start_date, end_date, notes FROM goals WHERE id = ?", (goal_id,)).fetchone()
        if not cur:
            conn.close()
            return False
        cur = dict(cur)
        goal_title = kwargs.get("goal_title", cur["goal_title"])
        goal_type = kwargs.get("goal_type", cur["goal_type"])
        target_value = kwargs.get("target_value", cur["target_value"])
        unit = kwargs.get("unit", cur["unit"])
        start_date = kwargs.get("start_date", cur["start_date"])
        end_date = kwargs.get("end_date", cur["end_date"])
        notes = kwargs.get("notes", cur["notes"])
        c.execute(""" UPDATE goals SET goal_title=?, goal_type=?, target_value=?, unit=?, start_date=?, end_date=?, notes=?  WHERE id=?""", (goal_title, goal_type, target_value, unit, start_date, end_date, notes, goal_id))
        conn.commit()
        conn.close()
        return True

    
    def delete_goal(self, goal_id: int) -> bool:
        """
        Delete a goal by id. Returns True if deleted, False if not found.
        This method delegates to db.delete_goal if available.
        """
        # Prefer using the db module if available
        try:
            if hasattr(db, "delete_goal"):
                return db.delete_goal(goal_id)
        except Exception:
            pass

        # Fallback: perform direct SQL delete using get_conn() if db.delete_goal doesn't exist
        try:
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT id FROM goals WHERE id = ?", (goal_id,))
            if not c.fetchone():
                conn.close()
                return False
            c.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            # bubble up or log — here we re-raise so caller can show an error message
            raise
        return db.list_fitness_records(user_id, limit)
