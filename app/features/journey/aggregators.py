"""
app.features.journey.aggregators — Logic for pulling data from other repositories
to build the state for the Journey Engine.
"""
from datetime import datetime, date
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.services.repositories import (
    HealthRepository,
    MealRepository,
    MedicationRepository,
    ReminderRepository,
    RiskFlagRepository,
    WorkflowRepository,
)
from app.features.journey.models import JourneyTask, RiskAlert, CompletionStatus, NextAction
from app.features.journey.rules import (
    get_profile_tasks,
    get_medication_tasks,
    get_monitoring_tasks,
    get_report_tasks,
)
from app.ui.navigation import PAGE_CHAT, PAGE_REPORTS

def aggregate_tasks(db: Session, patient_id: int) -> List[JourneyTask]:
    tasks = []
    
    # ── Modular Rules ───────────────────────────────────────────
    tasks.extend(get_profile_tasks(db, patient_id))
    tasks.extend(get_medication_tasks(db, patient_id))
    tasks.extend(get_monitoring_tasks(db, patient_id))
    tasks.extend(get_report_tasks(db, patient_id))

    return tasks

def aggregate_alerts(db: Session, patient_id: int) -> List[RiskAlert]:
    alerts = []
    
    # ── Active Risk Flags ────────────────────────────────────────
    risk_repo = RiskFlagRepository(db, patient_id)
    active_risks = risk_repo.list_active()
    
    for risk in active_risks:
        alerts.append(RiskAlert(
            id=f"risk_{risk.id}",
            type=risk.flag_type,
            title=f"风险提示: {risk.flag_type}",
            description=risk.description,
            severity=risk.severity,
            occurred_at=risk.created_at
        ))
        
    return alerts

def aggregate_completion(db: Session, patient_id: int) -> List[CompletionStatus]:
    stats = []
    
    # ── Medication Adherence ─────────────────────────────────────
    reminder_repo = ReminderRepository(db, patient_id)
    today_reminders = reminder_repo.list_today()
    if today_reminders:
        total = len(today_reminders)
        completed = len([r for r in today_reminders if r.status == "taken"])
        stats.append(CompletionStatus(
            category="用药",
            completed=completed,
            total=total,
            percentage=round(completed/total * 100, 1) if total > 0 else 0
        ))
    else:
        stats.append(CompletionStatus(category="用药", completed=0, total=0, percentage=0))

    # ── Health Recording ──────────────────────────────────────────
    # Let's say we expect 2 records (morning glucose, morning BP)
    health_repo = HealthRepository(db, patient_id)
    today_records = [e for e in health_repo.list_recent(20) if e.created_at.date() == date.today()]
    # simplified: target=2
    stats.append(CompletionStatus(
        category="病情监测",
        completed=min(len(today_records), 2),
        total=2,
        percentage=min(len(today_records)/2 * 100, 100)
    ))
    
    return stats

def suggest_next_action(tasks: List[JourneyTask], alerts: List[RiskAlert]) -> NextAction:
    if alerts:
        # If critical alert, suggest handling it
        critical = [a for a in alerts if a.severity == "critical"]
        if critical:
            return NextAction(
                label="由于风险高，建议联系医生",
                action_type="link",
                payload={"page": PAGE_CHAT, "prompt": f"解释风险: {critical[0].description}"},
                reason="检测到高危健康风险，请优先关注。"
            )

    if tasks:
        # Suggest the highest urgency task
        high_urgency = [t for t in tasks if t.urgency == "high"]
        target_task = high_urgency[0] if high_urgency else tasks[0]
        return NextAction(
            label=f"下一步: {target_task.title}",
            action_type=target_task.action_type,
            payload=target_task.action_payload,
            reason="完成此任务可提高今天的健康达成率。"
        )

    return NextAction(
        label="查看本周总结",
        action_type="link",
        payload={"page": PAGE_REPORTS},
        reason="所有今日基础任务均已完成，您可以回顾本周进展。"
    )
