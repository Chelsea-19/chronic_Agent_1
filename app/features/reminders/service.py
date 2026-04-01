"""
app.features.reminders.service — Medication reminder service.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.services.repositories import MedicationRepository, ReminderRepository


class ReminderService:
    def __init__(self, db: Session, patient_id: int):
        self.med_repo = MedicationRepository(db, patient_id)
        self.repo = ReminderRepository(db, patient_id)

    def generate_today(self):
        today = date.today()
        created = []
        for med in self.med_repo.list_active():
            item = self.repo.create_if_missing(med.id, today, med.schedule)
            if item is not None:
                created.append(item)
        return created

    def list_today(self):
        return self.repo.list_today()

    def update_status(self, occurrence_id: int, status: str):
        return self.repo.update_status(occurrence_id, status)

    def pending_count(self) -> int:
        return self.repo.pending_count()
