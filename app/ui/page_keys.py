"""Stable page-key constants and compatibility helpers."""

PAGE_HOME = "home"
PAGE_CHAT = "chat"
PAGE_MEDS = "meds"
PAGE_REPORTS = "reports"

DEFAULT_PAGE = PAGE_HOME

LEGACY_PAGE_ALIASES = {
    "🏠 今日旅程": PAGE_HOME,
    "💬 助手中心": PAGE_CHAT,
    "💊 用药管理": PAGE_MEDS,
    "📋 健康报告": PAGE_REPORTS,
    "智能对话": PAGE_CHAT,
}


def normalize_page_key(page_key: str | None) -> str:
    return LEGACY_PAGE_ALIASES.get(page_key, page_key) if page_key else DEFAULT_PAGE
