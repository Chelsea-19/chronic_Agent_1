"""Stable page-key constants for CarePilot CN."""

# Primary Pages
PAGE_HOME = "home"
PAGE_CHAT = "chat"
PAGE_MEDS = "meds"

# Secondary/Specialty Pages
PAGE_REPORTS = "reports"
PAGE_SETTINGS = "settings"
PAGE_TIMELINE = "timeline"
PAGE_WORKFLOWS = "workflows"
PAGE_PATIENTS = "patients"

DEFAULT_PAGE = PAGE_HOME

# Mapping for legacy or LLM-generated string keys
# This allows the system to be resilient to old string-based navigation
LEGACY_PAGE_MAPPING = {
    "🏠 今日旅程": PAGE_HOME,
    "💬 助手中心": PAGE_CHAT,
    "💊 用药管理": PAGE_MEDS,
    "📋 健康报告": PAGE_REPORTS,
    "智能对话": PAGE_CHAT,
    "dashboard": PAGE_HOME,
    "medication": PAGE_MEDS,
}
