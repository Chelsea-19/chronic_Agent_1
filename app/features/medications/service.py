"""
app.features.medications.service — Medication management.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.repositories import MedicationRepository


class MedicationService:
    def __init__(self, db: Session, patient_id: int):
        self.repo = MedicationRepository(db, patient_id)

    def create(self, medicine_name: str, dose: str, schedule: str, notes: str):
        return self.repo.create(medicine_name=medicine_name, dose=dose, schedule=schedule, notes=notes)

    def list_active(self):
        return self.repo.list_active()

    def deactivate(self, med_id: int):
        self.repo.deactivate(med_id)
