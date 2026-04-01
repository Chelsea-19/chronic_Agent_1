"""
app.features.meals.service — Meal analysis and tracking.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.services.parser import detect_meal_risks, estimate_meal_metrics
from app.services.repositories import MealRepository


@dataclass
class MealAnalyzeRequest:
    description: str
    meal_time: str = "auto"
    source: str = "text"


class MealService:
    def __init__(self, db: Session, patient_id: int):
        self.repo = MealRepository(db, patient_id)

    def analyze_and_record(self, payload: MealAnalyzeRequest):
        tags = detect_meal_risks(payload.description)
        carbs, sodium = estimate_meal_metrics(payload.description)
        row = self.repo.create(
            meal_time=payload.meal_time,
            description=payload.description,
            risk_tags="、".join(tags),
            estimated_carbs=carbs,
            estimated_sodium_mg=sodium,
            source=payload.source,
        )
        return {
            "record": row,
            "analysis": {
                "risk_tags": tags,
                "estimated_carbs": carbs,
                "estimated_sodium_mg": sodium,
                "advice": "建议优先控制主食量、含糖饮料和高盐菜品，并关注餐后血糖。",
            },
        }

    def list_records(self, limit: int = 50):
        return self.repo.list_recent(limit)

    def _summary(self, days: int, window: str) -> dict:
        rows = self.repo.list_within_days(days)
        tag_counter = Counter(tag for row in rows for tag in row.risk_tags.split("、") if tag)
        avg_carbs = sum((r.estimated_carbs or 0) for r in rows) / len(rows) if rows else None
        avg_sodium = sum((r.estimated_sodium_mg or 0) for r in rows) / len(rows) if rows else None
        return {
            "window": window,
            "total_records": len(rows),
            "top_risk_tags": [k for k, _ in tag_counter.most_common(5)],
            "avg_estimated_carbs": avg_carbs,
            "avg_estimated_sodium_mg": avg_sodium,
        }

    def daily_summary(self):
        return self._summary(1, "daily")

    def weekly_summary(self):
        return self._summary(7, "weekly")
