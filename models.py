# models.py
"""
SQLAlchemy models and DB helpers for Healthcare Monitoring AI Agent.
Provides: User, Medication, HealthRecord, FitnessRecord,
and helpers get_engine_and_session(), init_db().
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone
import os
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, create_engine, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Base declarative class
Base = declarative_base()

# Models (match your sqlite tables)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    dob = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    medications = relationship("Medication", back_populates="user", cascade="all, delete-orphan")
    health_records = relationship("HealthRecord", back_populates="user", cascade="all, delete-orphan")
    fitness_records = relationship("FitnessRecord", back_populates="user", cascade="all, delete-orphan")


    # relationships
    medications = relationship("Medication", back_populates="user", cascade="all, delete-orphan")
    health_records = relationship("HealthRecord", back_populates="user", cascade="all, delete-orphan")
    fitness_records = relationship("FitnessRecord", back_populates="user", cascade="all, delete-orphan")

class Medication(Base):
    __tablename__ = "medications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    dose = Column(String, nullable=True)
    time = Column(String, nullable=False)  # "HH:MM"
    frequency = Column(String, default="Daily")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="medications")

class HealthRecord(Base):
    __tablename__ = "health_records"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    type = Column(String, nullable=False)   # 'bp', 'sugar', etc.
    value = Column(String, nullable=False)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="health_records")

class FitnessRecord(Base):
    __tablename__ = "fitness_records"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    steps = Column(Integer, nullable=True)
    calories = Column(Integer, nullable=True)
    date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="fitness_records")


# DB helpers
DB_PATH = os.getenv("DB_PATH", "sqlite:///meds.db")

def get_engine_and_session(db_path: str = DB_PATH):
    connect_args = {}
    if db_path.startswith("sqlite:///"):
        connect_args = {"check_same_thread": False}
    engine = create_engine(db_path, connect_args=connect_args)
    SessionLocal = sessionmaker(bind=engine)
    return engine, SessionLocal

def init_db(db_path: str = DB_PATH):
    engine, _ = get_engine_and_session(db_path)
    Base.metadata.create_all(engine)
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    dose = Column(String, nullable=True)
    times = Column(String, nullable=True)        # comma-separated times
    frequency = Column(String, nullable=True, default="Daily")
    notes = Column(Text, nullable=True, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="medications")


class HealthRecord(Base):
    __tablename__ = "health_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=True)
    value = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="health_records")


class FitnessRecord(Base):
    __tablename__ = "fitness_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    steps = Column(Integer, nullable=True)
    calories = Column(Integer, nullable=True)
    date = Column(DateTime, nullable=True)  # column named 'date' in ORM; db may use record_date in raw sqlite
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="fitness_records")


class MedTaken(Base):
    __tablename__ = "med_taken"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False)
    taken_at = Column(DateTime, default=datetime.utcnow)
    note = Column(Text, nullable=True)


# Helper to create engine/session
def get_engine_and_session(db_url: Optional[str] = None):
    """
    Return (engine, SessionLocal). Default uses sqlite file 'health.db' in CWD
    or env var DB_PATH if specified by your other code.
    """
    if db_url is None:
        import os
        db_path = os.getenv("DB_PATH", "sqlite:///health.db")
        # ensure we accept both "health.db" and sqlite:///health.db
        if db_path == "health.db":
            db_url = "sqlite:///health.db"
        else:
            db_url = db_path
    engine = create_engine(db_url, connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {})
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return engine, SessionLocal


def init_db(db_url: Optional[str] = None):
    engine, _ = get_engine_and_session(db_url)
    # create all tables if they do not exist
    Base.metadata.create_all(bind=engine)
