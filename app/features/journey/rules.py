"""
app.features.journey.rules — Business logic for journey task generation.
"""
from datetime import date, datetime, timedelta
from typing import List
from sqlalchemy.orm import Session

from app.features.journey.models import JourneyTask, RiskAlert
from app.services.repositories import (
    HealthRepository,
    MedicationRepository,
    ReminderRepository,
    PatientRepository,
    MealRepository,
    RiskFlagRepository,
)
from app.ui.navigation import PAGE_CHAT, PAGE_HOME, PAGE_MEDS, PAGE_REPORTS

def get_profile_tasks(db: Session, patient_id: int) -> List[JourneyTask]:
    tasks = []
    patient_repo = PatientRepository(db)
    patient = patient_repo.get(patient_id)
    
    if patient and (not patient.age or not patient.medical_history):
        tasks.append(JourneyTask(
            id="complete_profile",
            title="完善个人健康档案",
            reason="完整的病史和基本信息能帮助 AI 提供更精准的个性化建议。",
            urgency="medium",
            effort="3 分钟",
            status="pending",
            action_type="link",
            action_payload={"page": PAGE_HOME}
        ))
    return tasks

def get_medication_tasks(db: Session, patient_id: int) -> List[JourneyTask]:
    tasks = []
    med_repo = MedicationRepository(db, patient_id)
    remind_repo = ReminderRepository(db, patient_id)
    
    active_plans = med_repo.list_active()
    if not active_plans:
        tasks.append(JourneyTask(
            id="add_medication",
            title="添加当前的用药计划",
            reason="记录您的用药方案，AI 可以为您提供准时的服药提醒和冲突检查。",
            urgency="high",
            effort="2 分钟",
            status="pending",
            action_type="link",
            action_payload={"page": PAGE_MEDS}
        ))
    else:
        pending_count = remind_repo.pending_count()
        if pending_count > 0:
            tasks.append(JourneyTask(
                id="confirm_medications",
                title="确认今日服药记录",
                reason=f"您今天还有 {pending_count} 次服药尚未进行线上确认。",
                urgency="high",
                effort="1 分钟",
                status="pending",
                action_type="link",
                action_payload={"page": PAGE_MEDS}
            ))
            
    return tasks

def get_monitoring_tasks(db: Session, patient_id: int) -> List[JourneyTask]:
    tasks = []
    health_repo = HealthRepository(db, patient_id)
    today = date.today()
    
    # Check for glucose
    events = health_repo.list_within_days(1)
    has_glucose = any(e.event_type == "血糖" and e.created_at.date() == today for e in events)
    if not has_glucose:
        tasks.append(JourneyTask(
            id="log_glucose",
            title="记录今日血糖值",
            reason="规律的血糖监测是糖尿病管理的基石，特别是餐后或空腹指标。",
            urgency="medium",
            effort="1 分钟",
            status="pending",
            action_type="link",
            action_payload={"page": PAGE_CHAT, "prompt": "我要记录今日血糖"}
        ))
        
    return tasks

def get_report_tasks(db: Session, patient_id: int) -> List[JourneyTask]:
    tasks = []
    # If today is Sunday, suggest weekly review
    if date.today().weekday() == 6: # Sunday
        tasks.append(JourneyTask(
            id="weekly_review",
            title="回顾本周健康总结",
            reason="查看这一周的指标波动和完成情况，为下周制定更好的计划。",
            urgency="medium",
            effort="5 分钟",
            status="pending",
            action_type="link",
            action_payload={"page": PAGE_REPORTS}
        ))
    return tasks
