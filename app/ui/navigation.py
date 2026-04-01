"""Central page registry and navigation helpers for stable routing keys."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict

import streamlit as st

from app.ui.pages import (
    page_chat,
    page_dashboard,
    page_medications,
)

PAGE_HOME = "home"
PAGE_CHAT = "chat"
PAGE_MEDS = "meds"
PAGE_REPORTS = "reports"


@dataclass(frozen=True)
class PageDef:
    key: str
    label: str
    render: Callable[[], None]
    is_primary: bool = True


def _placeholder_page(title: str, description: str):
    def _render():
        st.subheader(title)
        st.info(description)
    return _render


PAGE_REGISTRY: Dict[str, PageDef] = {
    PAGE_HOME: PageDef(PAGE_HOME, "🏠 今日旅程", page_dashboard, True),
    PAGE_CHAT: PageDef(PAGE_CHAT, "💬 助手中心", page_chat, True),
    PAGE_MEDS: PageDef(PAGE_MEDS, "💊 用药管理", page_medications, True),
    PAGE_REPORTS: PageDef(
        PAGE_REPORTS,
        "📋 健康报告",
        _placeholder_page("📋 健康报告", "该模块正在稳定化中，演示版本暂未开放。"),
        False,
    ),
}

PRIMARY_PAGE_KEYS = [k for k, v in PAGE_REGISTRY.items() if v.is_primary]
SECONDARY_PAGE_KEYS = [k for k, v in PAGE_REGISTRY.items() if not v.is_primary]
DEFAULT_PAGE = PAGE_HOME

LEGACY_PAGE_ALIASES = {
    "🏠 今日旅程": PAGE_HOME,
    "💬 助手中心": PAGE_CHAT,
    "💊 用药管理": PAGE_MEDS,
    "📋 健康报告": PAGE_REPORTS,
    "智能对话": PAGE_CHAT,
}


def ensure_valid_page(page_key: str | None) -> str:
    mapped = LEGACY_PAGE_ALIASES.get(page_key, page_key)
    if mapped in PAGE_REGISTRY:
        return mapped
    return DEFAULT_PAGE


def go_to_page(page_key: str):
    st.session_state.current_page = ensure_valid_page(page_key)
    st.rerun()
