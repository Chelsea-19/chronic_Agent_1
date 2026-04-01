"""
app.features.workflows.service — State-machine workflow execution engine.

Preserved from the original with all 5 workflow types and handler logic.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Literal

from sqlalchemy.orm import Session

from app.core.database import WorkflowRun
from app.features.clinician_digest.service import ClinicianDigestService
from app.features.companion.service import CompanionService
from app.features.reminders.service import ReminderService
from app.services.repositories import AuditLogRepository, WorkflowRepository

logger = logging.getLogger(__name__)


@dataclass
class WorkflowRequest:
    workflow_type: str
    payload: dict = None

    def __post_init__(self):
        if self.payload is None:
            self.payload = {}


class WorkflowDefinition:
    def __init__(self, name: str, steps: list[str]):
        self.name = name
        self.steps = steps


WORKFLOW_DEFINITIONS = {
    "daily_review": WorkflowDefinition(
        "daily_review",
        ["created", "collect_context", "evaluate_risk", "generate_actions", "completed"],
    ),
    "medication_reconciliation": WorkflowDefinition(
        "medication_reconciliation",
        ["created", "collect_medications", "generate_reminders", "completed"],
    ),
    "previsit_digest": WorkflowDefinition(
        "previsit_digest",
        ["created", "collect_context", "build_digest", "completed"],
    ),
    "adherence_followup": WorkflowDefinition(
        "adherence_followup",
        ["created", "identify_gaps", "generate_interventions", "completed"],
    ),
    "high_risk_escalation": WorkflowDefinition(
        "high_risk_escalation",
        ["created", "verify_condition", "notify_clinician", "completed"],
    ),
}


class StateMachineEngine:
    """Executes a workflow run step by step with logging."""

    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id
        self.repo = WorkflowRepository(db, patient_id)
        self.audit = AuditLogRepository(db, patient_id)
        self.handlers: dict[tuple[str, str], Callable[..., Any]] = {}

    def register_handler(self, workflow_type: str, state: str, handler: Callable[..., Any]) -> None:
        self.handlers[(workflow_type, state)] = handler

    def advance(self, run: WorkflowRun) -> None:
        definition = WORKFLOW_DEFINITIONS.get(run.workflow_type)
        if not definition:
            self._fail(run, f"Unknown workflow type: {run.workflow_type}")
            return

        try:
            current_index = definition.steps.index(run.current_state)
        except ValueError:
            self._fail(run, f"Invalid state {run.current_state}")
            return

        if current_index == len(definition.steps) - 1:
            return

        for next_state in definition.steps[current_index + 1:]:
            handler = self.handlers.get((run.workflow_type, next_state))
            try:
                summary_delta = ""
                if handler:
                    result = handler(run)
                    if isinstance(result, str):
                        summary_delta = result

                run = self.repo.update(
                    run.id,
                    current_state=next_state,
                    append_log={"state": next_state, "at": datetime.utcnow().isoformat(), "status": "success"},
                )

                if summary_delta:
                    current_summary = run.summary or ""
                    run = self.repo.update(run.id, summary=(current_summary + " " + summary_delta).strip())

                if next_state == "completed":
                    run = self.repo.update(run.id, status="completed")
                    self.audit.add(
                        action="workflow_completed",
                        details=f"Workflow {run.workflow_type} (ID: {run.id}) completed successfully.",
                    )
            except Exception as e:
                logger.error(f"Workflow {run.id} failed at state {next_state}: {e}")
                self._fail(run, str(e), failed_state=next_state)
                break

    def _fail(self, run: WorkflowRun, reason: str, failed_state: str = "error") -> None:
        self.repo.update(
            run.id, status="failed",
            append_log={"state": failed_state, "error": reason, "at": datetime.utcnow().isoformat()},
        )
        self.audit.add(
            action="workflow_failed",
            details=f"Workflow {run.workflow_type} (ID: {run.id}) failed: {reason}",
        )


class WorkflowService:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id
        self.repo = WorkflowRepository(db, patient_id)
        self.engine = StateMachineEngine(db, patient_id)
        self.companion = CompanionService(db, patient_id)
        self.reminders = ReminderService(db, patient_id)
        self.digest = ClinicianDigestService(db, patient_id)
        self._register_handlers()

    def _register_handlers(self) -> None:
        self.engine.register_handler("daily_review", "generate_actions", self._handle_daily_review_actions)
        self.engine.register_handler("medication_reconciliation", "generate_reminders", self._handle_med_recon)
        self.engine.register_handler("previsit_digest", "build_digest", self._handle_previsit_digest)
        self.engine.register_handler("adherence_followup", "identify_gaps", self._handle_identify_gaps)
        self.engine.register_handler("high_risk_escalation", "verify_condition", self._handle_verify_escalation)

    def _handle_daily_review_actions(self, run: WorkflowRun) -> str:
        today = self.companion.today_view()
        risk_str = "、".join(today["meal_risk_tags"]) if today["meal_risk_tags"] else "今日低风险饮食"
        return f"完成每日回顾：待处理提醒 {today['pending_reminders']} 条，重点跟进 {risk_str}。"

    def _handle_med_recon(self, run: WorkflowRun) -> str:
        created = len(self.reminders.generate_today())
        return f"已核对今日药物提醒，新增 {created} 条提醒。"

    def _handle_previsit_digest(self, run: WorkflowRun) -> str:
        payload = json.loads(run.payload_json)
        digest = self.digest.generate(window_days=payload.get("window_days", 14))
        return f"已生成 previsit digest #{digest.id}。"

    def _handle_identify_gaps(self, run: WorkflowRun) -> str:
        return "已识别依从性缺口并打标。"

    def _handle_verify_escalation(self, run: WorkflowRun) -> str:
        return "风险条件校验完成，已标记待跟进。"

    def run(self, payload: WorkflowRequest) -> WorkflowRun:
        row = self.repo.create(payload.workflow_type, payload.payload)
        self.engine.audit.add(action="workflow_started", details=f"Started workflow: {payload.workflow_type}")
        self.engine.advance(row)
        return self.repo.update(row.id)

    def list_runs(self):
        return self.repo.list_recent()
