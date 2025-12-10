# models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime, os

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    dob = Column(String, nullable=True)
    phone = Column(String, nullable=True)

class Medication(Base):
    __tablename__ = "medications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    dose = Column(String, nullable=True)
    time = Column(String, nullable=False)  # "HH:MM"
    frequency = Column(String, default="Daily")
    notes = Column(Text, nullable=True)

class HealthRecord(Base):
    __tablename__ = "health_records"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)
    type = Column(String)   # 'bp', 'sugar', etc.
    value = Column(String)
    notes = Column(Text, nullable=True)

DB_PATH = os.getenv("DB_PATH", "sqlite:///meds.db")

def get_engine_and_session(db_path=DB_PATH):
    engine = create_engine(db_path, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine)
    return engine, SessionLocal

def init_db():
    engine, _ = get_engine_and_session()
    Base.metadata.create_all(engine)
