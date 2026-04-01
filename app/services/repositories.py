"""
app.services.repositories — Data-access repositories.

Preserved from the original chronic_agent/platform/repositories.py
with updated imports to use the new database module.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import (
    AuditLog,
    ChatMessage,
    ClinicalDigest,
    FollowUpVisit,
    HealthEvent,
    MealRecord,
    MedicationPlan,
    PatientProfile,
    ReminderOccurrence,
    ReportArtifact,
    RiskFlag,
    SupportTrace,
    WorkflowRun,
)


class ChatRepository:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id

    def add(self, role: str, content: str) -> ChatMessage:
        row = ChatMessage(patient_id=self.patient_id, role=role, content=content)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def recent(self, limit: int = 20) -> list[ChatMessage]:
        return list(
            self.db.query(ChatMessage)
            .filter(ChatMessage.patient_id == self.patient_id)
            .order_by(desc(ChatMessage.id))
            .limit(limit)
            .all()
        )[::-1]


class HealthRepository:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id

    def add_event(self, **kwargs) -> HealthEvent:
        row = HealthEvent(patient_id=self.patient_id, **kwargs)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_recent(self, limit: int = 50) -> list[HealthEvent]:
        return list(
            self.db.query(HealthEvent)
            .filter(HealthEvent.patient_id == self.patient_id)
            .order_by(desc(HealthEvent.created_at))
            .limit(limit)
            .all()
        )

    def list_within_days(self, days: int) -> list[HealthEvent]:
        since = datetime.utcnow() - timedelta(days=days)
        return list(
            self.db.query(HealthEvent)
            .filter(
                HealthEvent.patient_id == self.patient_id,
                HealthEvent.created_at >= since,
            )
            .order_by(HealthEvent.created_at.asc())
            .all()
        )


class MealRepository:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id

    def create(self, **kwargs) -> MealRecord:
        row = MealRecord(patient_id=self.patient_id, **kwargs)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_recent(self, limit: int = 50) -> list[MealRecord]:
        return list(
            self.db.query(MealRecord)
            .filter(MealRecord.patient_id == self.patient_id)
            .order_by(desc(MealRecord.created_at))
            .limit(limit)
            .all()
        )

    def list_within_days(self, days: int) -> list[MealRecord]:
        since = datetime.utcnow() - timedelta(days=days)
        return list(
            self.db.query(MealRecord)
            .filter(
                MealRecord.patient_id == self.patient_id,
                MealRecord.created_at >= since,
            )
            .order_by(MealRecord.created_at.asc())
            .all()
        )


class MedicationRepository:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id

    def create(self, medicine_name: str, dose: str, schedule: str, notes: str) -> MedicationPlan:
        row = MedicationPlan(
            patient_id=self.patient_id,
            medicine_name=medicine_name, dose=dose,
            schedule=schedule, notes=notes,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_active(self) -> list[MedicationPlan]:
        return list(
            self.db.query(MedicationPlan)
            .filter(
                MedicationPlan.patient_id == self.patient_id,
                MedicationPlan.active.is_(True),
            )
            .order_by(MedicationPlan.id.desc())
            .all()
        )

    def deactivate(self, med_id: int) -> None:
        row = self.db.get(MedicationPlan, med_id)
        if row and row.patient_id == self.patient_id:
            row.active = False
            self.db.commit()


class ReminderRepository:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id

    def list_today(self) -> list[ReminderOccurrence]:
        today = date.today()
        return list(
            self.db.query(ReminderOccurrence)
            .filter(
                ReminderOccurrence.patient_id == self.patient_id,
                ReminderOccurrence.scheduled_for == today,
            )
            .order_by(ReminderOccurrence.id.desc())
            .all()
        )

    def create_if_missing(self, medication_id: int, scheduled_for: date, schedule_label: str) -> ReminderOccurrence | None:
        exists = (
            self.db.query(ReminderOccurrence)
            .filter(
                ReminderOccurrence.patient_id == self.patient_id,
                ReminderOccurrence.medication_id == medication_id,
                ReminderOccurrence.scheduled_for == scheduled_for,
                ReminderOccurrence.schedule_label == schedule_label,
            )
            .first()
        )
        if exists:
            return None
        row = ReminderOccurrence(
            patient_id=self.patient_id,
            medication_id=medication_id,
            scheduled_for=scheduled_for,
            schedule_label=schedule_label,
            status="pending",
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update_status(self, occurrence_id: int, status: str) -> ReminderOccurrence | None:
        row = self.db.get(ReminderOccurrence, occurrence_id)
        if row and row.patient_id == self.patient_id:
            row.status = status
            self.db.commit()
            self.db.refresh(row)
            return row
        return None

    def pending_count(self) -> int:
        today = date.today()
        return (
            self.db.query(ReminderOccurrence)
            .filter(
                ReminderOccurrence.patient_id == self.patient_id,
                ReminderOccurrence.scheduled_for == today,
                ReminderOccurrence.status == "pending",
            )
            .count()
        )


class DigestRepository:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id

    def save(self, window_days: int, markdown: str) -> ClinicalDigest:
        row = ClinicalDigest(
            patient_id=self.patient_id,
            window_days=window_days,
            content_markdown=markdown,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row


class WorkflowRepository:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id

    def create(self, workflow_type: str, payload: dict) -> WorkflowRun:
        row = WorkflowRun(
            patient_id=self.patient_id,
            workflow_type=workflow_type,
            status="running",
            current_state="created",
            payload_json=json.dumps(payload, ensure_ascii=False),
            log_json="[]",
            summary="",
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update(
        self, run_id: int, *,
        status: str | None = None,
        current_state: str | None = None,
        summary: str | None = None,
        append_log: dict | None = None,
    ) -> WorkflowRun:
        row = self.db.get(WorkflowRun, run_id)
        if row is None or row.patient_id != self.patient_id:
            raise ValueError("workflow run not found")
        if status is not None:
            row.status = status
        if current_state is not None:
            row.current_state = current_state
        if summary is not None:
            row.summary = summary
        if append_log is not None:
            logs = json.loads(row.log_json or "[]")
            logs.append(append_log)
            row.log_json = json.dumps(logs, ensure_ascii=False)
        row.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_recent(self, limit: int = 20) -> list[WorkflowRun]:
        return list(
            self.db.query(WorkflowRun)
            .filter(WorkflowRun.patient_id == self.patient_id)
            .order_by(desc(WorkflowRun.created_at))
            .limit(limit)
            .all()
        )


class ReportRepository:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id

    def add(self, report_type: str, window_days: int, title: str, markdown: str) -> ReportArtifact:
        row = ReportArtifact(
            patient_id=self.patient_id,
            report_type=report_type,
            window_days=window_days,
            title=title,
            markdown=markdown,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def set_export_paths(self, report_id: int, **paths) -> ReportArtifact:
        row = self.db.get(ReportArtifact, report_id)
        if row is None or row.patient_id != self.patient_id:
            raise ValueError("report not found")
        for key, val in paths.items():
            setattr(row, key, val)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get(self, report_id: int) -> ReportArtifact | None:
        row = self.db.get(ReportArtifact, report_id)
        return row if row and row.patient_id == self.patient_id else None

    def list_recent(self, limit: int = 20) -> list[ReportArtifact]:
        return list(
            self.db.query(ReportArtifact)
            .filter(ReportArtifact.patient_id == self.patient_id)
            .order_by(desc(ReportArtifact.created_at))
            .limit(limit)
            .all()
        )


class PatientRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> PatientProfile:
        row = PatientProfile(**kwargs)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_all(self) -> list[PatientProfile]:
        return list(self.db.query(PatientProfile).order_by(PatientProfile.id.asc()).all())

    def get(self, patient_id: int) -> PatientProfile | None:
        return self.db.get(PatientProfile, patient_id)


class FollowUpRepository:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id

    def create(self, scheduled_for: date, purpose: str, notes: str, status: str) -> FollowUpVisit:
        row = FollowUpVisit(
            patient_id=self.patient_id,
            scheduled_for=scheduled_for, purpose=purpose,
            notes=notes, status=status,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_all(self) -> list[FollowUpVisit]:
        return list(
            self.db.query(FollowUpVisit)
            .filter(FollowUpVisit.patient_id == self.patient_id)
            .order_by(desc(FollowUpVisit.scheduled_for))
            .all()
        )


class TimelineRepository:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id

    def build(self, limit: int = 100) -> list[dict]:
        items: list[dict] = []
        for r in (
            self.db.query(HealthEvent)
            .filter(HealthEvent.patient_id == self.patient_id)
            .order_by(desc(HealthEvent.created_at))
            .limit(limit)
            .all()
        ):
            items.append({
                "item_type": "health_event",
                "occurred_at": r.created_at,
                "title": r.event_type,
                "detail": r.value_text or f"{r.value_num1 or ''} {r.unit}".strip(),
            })
        for r in (
            self.db.query(MealRecord)
            .filter(MealRecord.patient_id == self.patient_id)
            .order_by(desc(MealRecord.created_at))
            .limit(limit)
            .all()
        ):
            items.append({
                "item_type": "meal",
                "occurred_at": r.created_at,
                "title": r.meal_time,
                "detail": f"{r.description} | 风险:{r.risk_tags or '低'}",
            })
        for r in (
            self.db.query(ReminderOccurrence)
            .filter(ReminderOccurrence.patient_id == self.patient_id)
            .order_by(desc(ReminderOccurrence.created_at))
            .limit(limit)
            .all()
        ):
            items.append({
                "item_type": "reminder",
                "occurred_at": r.created_at,
                "title": r.schedule_label,
                "detail": f"{r.medication.medicine_name} | {r.status}",
            })
        for r in (
            self.db.query(ClinicalDigest)
            .filter(ClinicalDigest.patient_id == self.patient_id)
            .order_by(desc(ClinicalDigest.created_at))
            .limit(limit)
            .all()
        ):
            items.append({
                "item_type": "digest",
                "occurred_at": r.created_at,
                "title": f"门诊摘要 {r.window_days}天",
                "detail": r.content_markdown[:120],
            })
        for r in (
            self.db.query(FollowUpVisit)
            .filter(FollowUpVisit.patient_id == self.patient_id)
            .order_by(desc(FollowUpVisit.created_at))
            .limit(limit)
            .all()
        ):
            items.append({
                "item_type": "followup",
                "occurred_at": datetime.combine(r.scheduled_for, datetime.min.time()),
                "title": r.purpose,
                "detail": f"{r.status} | {r.notes}",
            })
        items.sort(key=lambda x: x["occurred_at"], reverse=True)
        return items[:limit]


class AuditLogRepository:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id

    def add(self, action: str, details: str = "", performed_by: str = "system") -> AuditLog:
        row = AuditLog(
            patient_id=self.patient_id,
            action=action, details=details, performed_by=performed_by,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row


class SupportTraceRepository:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id

    def add(
        self, target_entity: str, target_id: int | None,
        source_entity: str, source_id: int | None,
        evidence_snippet: str = "",
    ) -> SupportTrace:
        row = SupportTrace(
            patient_id=self.patient_id,
            target_entity=target_entity, target_id=target_id,
            source_entity=source_entity, source_id=source_id,
            evidence_snippet=evidence_snippet,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_for_target(self, target_entity: str, target_id: int) -> list[SupportTrace]:
        return list(
            self.db.query(SupportTrace)
            .filter(
                SupportTrace.patient_id == self.patient_id,
                SupportTrace.target_entity == target_entity,
                SupportTrace.target_id == target_id,
            )
            .all()
        )


class RiskFlagRepository:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id

    def add(self, flag_type: str, severity: str, description: str) -> RiskFlag:
        row = RiskFlag(
            patient_id=self.patient_id,
            flag_type=flag_type, severity=severity, description=description,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_active(self) -> list[RiskFlag]:
        return list(
            self.db.query(RiskFlag)
            .filter(
                RiskFlag.patient_id == self.patient_id,
                RiskFlag.is_active.is_(True),
            )
            .order_by(desc(RiskFlag.created_at))
            .all()
        )

    def resolve(self, flag_id: int) -> None:
        row = self.db.get(RiskFlag, flag_id)
        if row and row.patient_id == self.patient_id:
            row.is_active = False
            self.db.commit()
