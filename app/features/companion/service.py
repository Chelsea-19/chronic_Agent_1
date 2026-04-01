"""
app.features.companion.service — Companion dashboard and insights.
"""
from __future__ import annotations

from collections import Counter
from datetime import date

from sqlalchemy.orm import Session

from app.services.repositories import HealthRepository, MealRepository, MedicationRepository, ReminderRepository


class CompanionService:
    def __init__(self, db: Session, patient_id: int):
        self.health_repo = HealthRepository(db, patient_id)
        self.meal_repo = MealRepository(db, patient_id)
        self.med_repo = MedicationRepository(db, patient_id)
        self.reminder_repo = ReminderRepository(db, patient_id)

    def summary(self) -> dict:
        events = self.health_repo.list_recent(limit=50)
        latest_bp = next(
            (e for e in events if e.event_type == "blood_pressure" and e.value_num1 and e.value_num2), None
        )
        latest_fg = next(
            (e for e in events if e.event_type == "fasting_glucose" and e.value_num1 is not None), None
        )
        return {
            "date": date.today(),
            "latest_blood_pressure": (
                f"{latest_bp.value_num1:.0f}/{latest_bp.value_num2:.0f} mmHg" if latest_bp else None
            ),
            "latest_fasting_glucose": latest_fg.value_num1 if latest_fg else None,
            "active_medications": len(self.med_repo.list_active()),
            "pending_reminders": self.reminder_repo.pending_count(),
        }

    def today_view(self) -> dict:
        summary = self.summary()
        meal_tags = Counter(
            tag for row in self.meal_repo.list_within_days(1)
            for tag in row.risk_tags.split("、") if tag
        )
        coach = "今天建议优先完成服药、补齐晨间血压与空腹血糖，并尽量避免高糖饮料和高盐外卖。"
        if summary["pending_reminders"] == 0:
            coach = "今天的提醒都处理完了，接下来重点观察血糖血压趋势，并保持规律饮食。"
        return {
            **summary,
            "meal_risk_tags": list(meal_tags.keys()),
            "coach_message": coach,
        }

    def insights(self) -> dict:
        week_meals = self.meal_repo.list_within_days(7)
        meal_tag_counter = Counter(
            tag for row in week_meals for tag in row.risk_tags.split("、") if tag
        )
        return {
            "top_meal_risks": meal_tag_counter.most_common(5),
            "active_medications": len(self.med_repo.list_active()),
            "pending_reminders": self.reminder_repo.pending_count(),
            "suggestion": "若本周高糖或高盐标签频繁出现，建议优先从含糖饮料、主食量和外卖汤汁入手调整。",
        }
