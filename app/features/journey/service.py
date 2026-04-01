"""
app.features.journey.service — Orchestrating state aggregation
and generating journey guidance.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.features.journey.models import JourneyState
from app.features.journey.aggregators import (
    aggregate_tasks,
    aggregate_alerts,
    aggregate_completion,
    suggest_next_action,
)

class JourneyService:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id

    def get_state(self) -> JourneyState:
        tasks = aggregate_tasks(self.db, self.patient_id)
        alerts = aggregate_alerts(self.db, self.patient_id)
        completion = aggregate_completion(self.db, self.patient_id)
        next_action = suggest_next_action(tasks, alerts)
        
        # Greeting and Hero Logic
        hour = datetime.now().hour
        greeting = "早上好" if 5 <= hour < 12 else "下午好" if 12 <= hour < 18 else "晚上好"
        
        num_urgent = len([t for t in tasks if t.urgency == "high"])
        if num_urgent > 0:
            hero_message = f"您今天还有 {num_urgent} 项需要优先处理的健康任务。"
        elif tasks:
            hero_message = f"您今天仍有 {len(tasks)} 条健康建议可供参考。"
        else:
            hero_message = "您今天的所有核心计划和任务均已完成，保持出色状态！"

        return JourneyState(
            patient_id=self.patient_id,
            tasks=tasks,
            alerts=alerts,
            completion=completion,
            suggested_next_action=next_action,
            last_updated=datetime.now(),
            greeting=greeting,
            hero_message=hero_message
        )
