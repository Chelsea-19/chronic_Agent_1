"""
app.core.database — SQLAlchemy ORM models and DB init.

Adapted from the original chronic_agent/platform/db.py to use
portable paths and Streamlit-compatible initialization.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean, Date, DateTime, Float, ForeignKey,
    Integer, String, Text, create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column,
    relationship, sessionmaker, Session,
)

import streamlit as st

_engine = None
_SessionLocal = None


class Base(DeclarativeBase):
    pass


# ── ORM Models ───────────────────────────────────────────────────

class PatientProfile(Base):
    __tablename__ = "patient_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    gender: Mapped[str] = mapped_column(String(20), default="")
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    diagnosis_summary: Mapped[str] = mapped_column(String(200), default="2型糖尿病合并高血压")
    phone: Mapped[str] = mapped_column(String(50), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    role: Mapped[str] = mapped_column(String(20), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class HealthEvent(Base):
    __tablename__ = "health_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    value_text: Mapped[str] = mapped_column(Text, default="")
    value_num1: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_num2: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(20), default="")
    source: Mapped[str] = mapped_column(String(20), default="chat")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    provenance: Mapped[str] = mapped_column(String(200), default="")
    created_by: Mapped[str] = mapped_column(String(50), default="patient")
    system_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class MealRecord(Base):
    __tablename__ = "meal_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    meal_time: Mapped[str] = mapped_column(String(20), default="auto", index=True)
    description: Mapped[str] = mapped_column(Text)
    risk_tags: Mapped[str] = mapped_column(String(200), default="")
    estimated_carbs: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_sodium_mg: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="text")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    provenance: Mapped[str] = mapped_column(String(200), default="")
    created_by: Mapped[str] = mapped_column(String(50), default="patient")
    system_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class MedicationPlan(Base):
    __tablename__ = "medication_plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    medicine_name: Mapped[str] = mapped_column(String(100), index=True)
    dose: Mapped[str] = mapped_column(String(50), default="")
    schedule: Mapped[str] = mapped_column(String(100), default="早餐后")
    notes: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    occurrences: Mapped[list["ReminderOccurrence"]] = relationship(back_populates="medication")


class ReminderOccurrence(Base):
    __tablename__ = "reminder_occurrences"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    medication_id: Mapped[int] = mapped_column(ForeignKey("medication_plans.id"), index=True)
    scheduled_for: Mapped[date] = mapped_column(Date, index=True)
    schedule_label: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    medication: Mapped[MedicationPlan] = relationship(back_populates="occurrences")


class ClinicalDigest(Base):
    __tablename__ = "clinical_digests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    window_days: Mapped[int] = mapped_column(Integer)
    content_markdown: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    workflow_type: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    current_state: Mapped[str] = mapped_column(String(50), default="created")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    log_json: Mapped[str] = mapped_column(Text, default="[]")
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)


class ReportArtifact(Base):
    __tablename__ = "report_artifacts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    report_type: Mapped[str] = mapped_column(String(50), index=True)
    window_days: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    markdown: Mapped[str] = mapped_column(Text)
    docx_path: Mapped[str] = mapped_column(String(300), default="")
    pdf_path: Mapped[str] = mapped_column(String(300), default="")
    html_path: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class FollowUpVisit(Base):
    __tablename__ = "followup_visits"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    scheduled_for: Mapped[date] = mapped_column(Date, index=True)
    purpose: Mapped[str] = mapped_column(String(100), default="复诊")
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="planned")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    details: Mapped[str] = mapped_column(Text, default="")
    performed_by: Mapped[str] = mapped_column(String(50), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class SupportTrace(Base):
    __tablename__ = "support_traces"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    target_entity: Mapped[str] = mapped_column(String(50))
    target_id: Mapped[int] = mapped_column(Integer, nullable=True)
    source_entity: Mapped[str] = mapped_column(String(50))
    source_id: Mapped[int] = mapped_column(Integer, nullable=True)
    evidence_snippet: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class RiskFlag(Base):
    __tablename__ = "risk_flags"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    flag_type: Mapped[str] = mapped_column(String(50), index=True)
    severity: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


# ── Engine & Session ─────────────────────────────────────────────

def _get_engine():
    global _engine
    if _engine is None:
        from app.core.config import get_settings
        s = get_settings()
        _engine = create_engine(
            s.database_url,
            connect_args={"check_same_thread": False},
        )
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=_get_engine(), autocommit=False, autoflush=False
        )
    return _SessionLocal


def get_db() -> Session:
    """Return a new DB session (caller must close)."""
    factory = get_session_factory()
    return factory()


def init_db():
    """Create all tables and seed default patient if empty."""
    engine = _get_engine()
    Base.metadata.create_all(bind=engine)
    db = get_db()
    try:
        if db.query(PatientProfile).count() == 0:
            db.add(PatientProfile(
                name="默认患者", gender="未知",
                diagnosis_summary="2型糖尿病合并高血压"
            ))
            db.commit()
    finally:
        db.close()
