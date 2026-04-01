"""
app.ui.pages — Page module re-exports.
"""
from app.ui.pages.dashboard import page_dashboard
from app.ui.pages.chat import page_chat
from app.ui.pages.meals import page_meals
from app.ui.pages.medications import page_medications
from app.ui.pages.reminders import page_reminders
from app.ui.pages.reports import page_reports
from app.ui.pages.workflows import page_workflows
from app.ui.pages.patients import page_patients
from app.ui.pages.timeline import page_timeline
from app.ui.pages.settings import page_settings
from app.ui.pages.evaluation import page_evaluation

__all__ = [
    "page_dashboard", "page_chat", "page_meals", "page_medications",
    "page_reminders", "page_reports", "page_workflows", "page_patients",
    "page_timeline", "page_settings", "page_evaluation",
]
