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

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    dob = Column(String, nullable=True)
    phone = Column(String, nullable=True)

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