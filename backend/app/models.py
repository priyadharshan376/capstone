import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship
from app.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    INSPECTOR = "inspector"

class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class InspectionStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"

class FindingStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NA = "NA"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.INSPECTOR)
    badge_number = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    inspections = relationship("Inspection", back_populates="inspector")

class Facility(Base):
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    license_no = Column(String(100), unique=True, nullable=False)
    category = Column(String(100), nullable=False)  # Chemical, Food, Factory, Hospital, etc.
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    risk_level = Column(String(50), default=RiskLevel.MEDIUM)
    contact_person = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    inspections = relationship("Inspection", back_populates="facility")

class ChecklistTemplate(Base):
    __tablename__ = "checklist_templates"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("ChecklistItem", back_populates="template", cascade="all, delete-orphan")
    inspections = relationship("Inspection", back_populates="template")

class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("checklist_templates.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="pass_fail")  # pass_fail, rating, text
    is_required = Column(Boolean, default=True)
    order_index = Column(Integer, default=0)

    template = relationship("ChecklistTemplate", back_populates="items")
    findings = relationship("Finding", back_populates="checklist_item")

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    inspector_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    template_id = Column(Integer, ForeignKey("checklist_templates.id"), nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    status = Column(String(50), default=InspectionStatus.ASSIGNED)
    priority = Column(String(50), default="NORMAL")  # NORMAL, HIGH, CRITICAL
    
    # Evidence & Verification Data
    submission_notes = Column(Text, nullable=True)
    submission_lat = Column(Float, nullable=True)
    submission_lng = Column(Float, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    
    # Supervisor Review
    supervisor_feedback = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    facility = relationship("Facility", back_populates="inspections")
    inspector = relationship("User", back_populates="inspections")
    template = relationship("ChecklistTemplate", back_populates="inspections")
    findings = relationship("Finding", back_populates="inspection", cascade="all, delete-orphan")

class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    checklist_item_id = Column(Integer, ForeignKey("checklist_items.id"), nullable=False)
    status = Column(String(50), default=FindingStatus.PASS)  # PASS, FAIL, NA
    notes = Column(Text, nullable=True)
    photo_url = Column(String(500), nullable=True)
    gps_lat = Column(Float, nullable=True)
    gps_lng = Column(Float, nullable=True)
    captured_at = Column(DateTime, default=datetime.utcnow)

    inspection = relationship("Inspection", back_populates="findings")
    checklist_item = relationship("ChecklistItem", back_populates="findings")

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False)  # INSPECTION_CREATED, INSPECTION_ASSIGNED, etc.
    actor_id = Column(Integer, nullable=True)
    actor_name = Column(String(255), nullable=False)
    entity_type = Column(String(100), nullable=False)  # Inspection, Facility, User
    entity_id = Column(Integer, nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    hash_signature = Column(String(64), nullable=True)  # SHA-256 integrity hash
