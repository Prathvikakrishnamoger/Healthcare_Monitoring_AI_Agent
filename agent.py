# agent.py
from typing import List, Optional, Dict, Any
import db

# ensure DB/tables exist
try:
    db.init_db()
except Exception:
    pass

class HealthAgent:
    """Simple agent wrapper around db.py functions."""

    def _init_(self):
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