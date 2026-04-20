from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship as sql_relationship
from datetime import datetime
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    emergency_contacts = sql_relationship("EmergencyContact", back_populates="user", cascade="all, delete-orphan")
    medical_history = sql_relationship("MedicalHistory", back_populates="user", uselist=False, cascade="all, delete-orphan")

class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    relationship = Column(String, nullable=True)

    # Back reference to User
    user = sql_relationship("User", back_populates="emergency_contacts")

class MedicalHistory(Base):
    __tablename__ = "medical_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)
    conditions = Column(JSON, nullable=True)
    other = Column(Text, nullable=True)

    # Back reference to User
    user = sql_relationship("User", back_populates="medical_history")
