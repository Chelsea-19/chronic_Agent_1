"""
app.services.timeline — Longitudinal Timeline Engine.

Preserved from the original chronic_agent/core/timeline.py.
Aggregates patient events across categories for trend analysis.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import (
    ClinicalDigest, FollowUpVisit, HealthEvent,
    MealRecord, ReminderOccurrence,
)
from app.services.repositories import (
    HealthRepository, MealRepository,
    ReminderRepository, FollowUpRepository, DigestRepository,
)


class UnifiedEvent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    patient_id: int
    event_category: str  # 'health', 'meal', 'reminder', 'digest', 'followup'
    event_type: str
    occurred_at: datetime
    summary: str
    detail: dict[str, Any] = {}
    is_anomaly: bool = False
    confidence: float | None = None
    provenance: str = ""
    raw_reference: Any = None


class TimelineEngine:
    """
    Longitudinal timeline engine for chronologically retrieving,
    filtering, and tagging patient events for digestion and evaluation.
    """

    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id

    def extract_window(
        self, since: datetime, until: datetime | None = None,
        categories: list[str] | None = None,
    ) -> list[UnifiedEvent]:
        until = until or datetime.utcnow()
        events: list[UnifiedEvent] = []

        if not categories or "health" in categories:
            for r in (
                self.db.query(HealthEvent)
                .filter(
                    HealthEvent.patient_id == self.patient_id,
                    HealthEvent.created_at >= since,
                    HealthEvent.created_at <= until,
                )
                .all()
            ):
                is_anomaly = False
                if r.event_type == "blood_pressure" and r.value_num1 and r.value_num1 >= 140:
                    is_anomaly = True
                if r.event_type == "fasting_glucose" and r.value_num1 and r.value_num1 >= 7.0:
                    is_anomaly = True

                events.append(UnifiedEvent(
                    id=f"health_{r.id}",
                    patient_id=r.patient_id,
                    event_category="health",
                    event_type=r.event_type,
                    occurred_at=r.created_at,
                    summary=f"{r.value_text or (str(r.value_num1) + ' ' + (r.unit or ''))}".strip(),
                    detail={"num1": r.value_num1, "num2": r.value_num2, "unit": r.unit},
                    is_anomaly=is_anomaly,
                    confidence=r.confidence,
                    provenance=r.provenance,
                    raw_reference=r,
                ))

        if not categories or "meal" in categories:
            for r in (
                self.db.query(MealRecord)
                .filter(
                    MealRecord.patient_id == self.patient_id,
                    MealRecord.created_at >= since,
                    MealRecord.created_at <= until,
                )
                .all()
            ):
                is_anomaly = bool(r.risk_tags and r.risk_tags != "低")
                events.append(UnifiedEvent(
                    id=f"meal_{r.id}",
                    patient_id=r.patient_id,
                    event_category="meal",
                    event_type=r.meal_time,
                    occurred_at=r.created_at,
                    summary=r.description,
                    detail={"risk_tags": r.risk_tags, "carbs": r.estimated_carbs},
                    is_anomaly=is_anomaly,
                    confidence=r.confidence,
                    provenance=r.provenance,
                    raw_reference=r,
                ))

        if not categories or "reminder" in categories:
            for r in (
                self.db.query(ReminderOccurrence)
                .filter(ReminderOccurrence.patient_id == self.patient_id)
                .all()
            ):
                dt = datetime.combine(r.scheduled_for, datetime.min.time())
                if since <= dt <= until:
                    is_anomaly = r.status in ["skipped", "missed"]
                    events.append(UnifiedEvent(
                        id=f"reminder_{r.id}",
                        patient_id=r.patient_id,
                        event_category="reminder",
                        event_type=r.schedule_label,
                        occurred_at=dt,
                        summary=f"{r.medication.medicine_name} | {r.status}",
                        detail={"status": r.status},
                        is_anomaly=is_anomaly,
                        raw_reference=r,
                    ))

        if not categories or "followup" in categories:
            for r in (
                self.db.query(FollowUpVisit)
                .filter(FollowUpVisit.patient_id == self.patient_id)
                .all()
            ):
                dt = datetime.combine(r.scheduled_for, datetime.min.time())
                if since <= dt <= until:
                    events.append(UnifiedEvent(
                        id=f"followup_{r.id}",
                        patient_id=r.patient_id,
                        event_category="followup",
                        event_type=r.purpose,
                        occurred_at=dt,
                        summary=f"{r.status} | {r.notes}",
                        detail={"status": r.status, "notes": r.notes},
                        raw_reference=r,
                    ))

        events.sort(key=lambda x: x.occurred_at)
        return events

    def extract_trend(self, since: datetime, until: datetime | None = None) -> dict[str, Any]:
        """Longitudinal pattern extraction over a window."""
        until = until or datetime.utcnow()
        events = self.extract_window(since, until, categories=["health", "meal", "reminder"])

        bp_events = [e for e in events if e.event_category == "health" and e.event_type == "blood_pressure"]
        fg_events = [e for e in events if e.event_category == "health" and e.event_type == "fasting_glucose"]
        meal_anomalies = [e for e in events if e.event_category == "meal" and e.is_anomaly]
        reminder_missed = [e for e in events if e.event_category == "reminder" and e.is_anomaly]

        avg_sys = sum((e.detail.get("num1") or 0) for e in bp_events) / len(bp_events) if bp_events else None
        avg_dia = sum((e.detail.get("num2") or 0) for e in bp_events) / len(bp_events) if bp_events else None
        avg_fg = sum((e.detail.get("num1") or 0) for e in fg_events) / len(fg_events) if fg_events else None

        return {
            "window_days": (until - since).days if until else 0,
            "blood_pressure": {"avg_sys": avg_sys, "avg_dia": avg_dia, "count": len(bp_events)},
            "fasting_glucose": {"avg": avg_fg, "count": len(fg_events)},
            "meal_risks": len(meal_anomalies),
            "adherence_misses": len(reminder_missed),
            "total_anomalies": sum(1 for e in events if e.is_anomaly),
        }
