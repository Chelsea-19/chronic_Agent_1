"""
app.features.patients.service — Patient management service.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.repositories import FollowUpRepository, PatientRepository, TimelineRepository


class PatientService:
    def __init__(self, db: Session):
        self.patient_repo = PatientRepository(db)
        self.db = db

    def create_patient(self, name: str, gender: str = "", age: int | None = None,
                       diagnosis_summary: str = "2型糖尿病合并高血压", phone: str = ""):
        return self.patient_repo.create(
            name=name, gender=gender, age=age,
            diagnosis_summary=diagnosis_summary, phone=phone,
        )

    def list_patients(self):
        return self.patient_repo.list_all()

    def get_patient(self, patient_id: int):
        return self.patient_repo.get(patient_id)

    def create_followup(self, patient_id: int, scheduled_for, purpose: str = "复诊",
                        notes: str = "", status: str = "planned"):
        return FollowUpRepository(self.db, patient_id).create(
            scheduled_for=scheduled_for, purpose=purpose,
            notes=notes, status=status,
        )

    def list_followups(self, patient_id: int):
        return FollowUpRepository(self.db, patient_id).list_all()

    def timeline(self, patient_id: int):
        return TimelineRepository(self.db, patient_id).build()
