"""
app.services.tools — Tool Registry for the Agent Orchestrator.

Preserved from the original chronic_agent/agent/tool_registry.py.
All tools operate on the service layer, not on API routes.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from app.features.patients.service import PatientService
from app.features.health.service import HealthTrackingService
from app.features.medications.service import MedicationService
from app.features.reminders.service import ReminderService
from app.features.clinician_digest.service import ClinicianDigestService
from app.features.meals.service import MealService
from app.features.workflows.service import WorkflowService
from app.features.reports.service import ReportService
from app.services.repositories import HealthRepository

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id
        self._tools: dict[str, dict[str, Any]] = {}
        self._register_all_tools()

    def _register_all_tools(self):
        self.register_tool(
            name="get_today_overview",
            func=self.get_today_overview,
            description="获取患者今日的健康指标概览，包括最新的血压、血糖、用药和提醒情况。",
        )
        self.register_tool(
            name="record_health_event",
            func=self.record_health_event,
            description="记录血压、血糖、体重、症状或随笔记录。输入应包含数值和单位。",
            parameters={"raw_text": "包含健康数据的原始文本"},
        )
        self.register_tool(
            name="list_medications",
            func=self.list_medications,
            description="列出当前患者正在服用的所有药物及其剂量和频次。",
        )
        self.register_tool(
            name="add_medication",
            func=self.add_medication,
            description="为患者添加一种新药。需提供药名、剂量和服药时间。",
            parameters={"medicine_name": "药名", "dose": "剂量", "schedule": "执行计划，如'早餐后'", "notes": "备注信息"},
        )
        self.register_tool(
            name="analyze_meal",
            func=self.analyze_meal,
            description="分析患者的一顿饮食，评估风险（高糖、高碳水、高脂、高盐）。",
            parameters={"description": "饮食内容的文字描述"},
        )
        self.register_tool(
            name="get_weekly_meal_summary",
            func=self.get_weekly_meal_summary,
            description="获取过去一周的饮食营养与风险总结。",
        )
        self.register_tool(
            name="generate_reminders",
            func=self.generate_reminders,
            description="基于用药计划，为今天生成待执行的服药提醒。",
        )
        self.register_tool(
            name="run_workflow",
            func=self.run_workflow,
            description="执行特定的自动化管理流程，如'daily_review', 'medication_reconciliation', 'previsit_digest'。",
            parameters={"workflow_type": "工作流类型"},
        )
        self.register_tool(
            name="generate_digest",
            func=self.generate_digest,
            description="生成包含近期趋势分析的临床摘要（Markdown格式），用于医生参考。",
        )
        self.register_tool(
            name="generate_report",
            func=self.generate_report,
            description="生成正式的PDF/Markdown健康报告。",
            parameters={"report_type": "报告类型", "window_days": "覆盖的天数(整数)"},
        )
        self.register_tool(
            name="get_timeline",
            func=self.get_timeline,
            description="获取患者的所有历史健康事件、用药变更和报告时间线。",
        )

    def register_tool(self, name: str, func: Callable, description: str, parameters: Optional[dict] = None):
        self._tools[name] = {
            "name": name,
            "func": func,
            "description": description,
            "parameters": parameters or {},
        }

    def get_tool_metadata(self) -> list[dict[str, Any]]:
        return [
            {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}
            for t in self._tools.values()
        ]

    def call_tool(self, name: str, **kwargs) -> Any:
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found")
        logger.info(f"Executing tool: {name} with args: {kwargs}")
        return self._tools[name]["func"](**kwargs)

    # ── Tool Implementations ─────────────────────────────

    def get_today_overview(self):
        repo = HealthRepository(self.db, self.patient_id)
        events = repo.list_recent(limit=50)
        latest_bp = next((e for e in events if e.event_type == "blood_pressure" and e.value_num1 and e.value_num2), None)
        latest_fg = next((e for e in events if e.event_type == "fasting_glucose" and e.value_num1 is not None), None)
        meds = MedicationService(self.db, self.patient_id).list_active()
        reminders = ReminderService(self.db, self.patient_id).list_today()

        return {
            "latest_bp": f"{latest_bp.value_num1:.0f}/{latest_bp.value_num2:.0f}" if latest_bp else "未录入",
            "latest_fasting_glucose": latest_fg.value_num1 if latest_fg else "未录入",
            "active_medication_count": len(meds),
            "pending_reminders": len([r for r in reminders if r.status == "pending"]),
        }

    def record_health_event(self, raw_text: str = ""):
        return HealthTrackingService(self.db, self.patient_id).track_from_chat(raw_text)

    def list_medications(self):
        rows = MedicationService(self.db, self.patient_id).list_active()
        return [{"name": r.medicine_name, "dose": r.dose, "schedule": r.schedule} for r in rows]

    def add_medication(self, medicine_name: str, dose: str = "", schedule: str = "早餐后", notes: str = ""):
        return MedicationService(self.db, self.patient_id).create(
            medicine_name=medicine_name, dose=dose, schedule=schedule, notes=notes,
        )

    def analyze_meal(self, description: str):
        from app.features.meals.service import MealAnalyzeRequest
        payload = MealAnalyzeRequest(description=description)
        return MealService(self.db, self.patient_id).analyze_and_record(payload)

    def get_weekly_meal_summary(self):
        return MealService(self.db, self.patient_id).weekly_summary()

    def generate_reminders(self):
        return ReminderService(self.db, self.patient_id).generate_today()

    def run_workflow(self, workflow_type: str):
        from app.features.workflows.service import WorkflowRequest
        payload = WorkflowRequest(workflow_type=workflow_type)
        return WorkflowService(self.db, self.patient_id).run(payload)

    def generate_digest(self):
        row = ClinicianDigestService(self.db, self.patient_id).generate(window_days=14)
        return {"id": row.id, "summary": row.content_markdown[:200] + "..."}

    def generate_report(self, report_type: str = "clinician_previsit", window_days: int = 14):
        from app.features.reports.service import ReportRequest
        payload = ReportRequest(report_type=report_type, window_days=int(window_days))
        return ReportService(self.db, self.patient_id).generate(payload)

    def get_timeline(self):
        items = PatientService(self.db).timeline(self.patient_id)
        return [{"time": str(i["occurred_at"]), "type": i["item_type"], "title": i["title"]} for i in items[:10]]
