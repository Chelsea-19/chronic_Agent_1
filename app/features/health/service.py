"""
app.features.health.service — Health event tracking.
"""
from __future__ import annotations

from dataclasses import asdict

from sqlalchemy.orm import Session

from app.services.parser import detect_meal_risks, parse_track_message
from app.services.repositories import HealthRepository


class HealthTrackingService:
    def __init__(self, db: Session, patient_id: int):
        self.repo = HealthRepository(db, patient_id)

    def track_from_chat(self, raw_message: str):
        parsed = parse_track_message(raw_message)
        event = self.repo.add_event(**asdict(parsed))
        if parsed.event_type == "meal":
            tags = detect_meal_risks(parsed.value_text)
            if tags:
                self.repo.add_event(event_type="meal_risk", value_text="、".join(tags), source="derived")
        return event

    def list_recent(self, limit: int = 50):
        return self.repo.list_recent(limit)
