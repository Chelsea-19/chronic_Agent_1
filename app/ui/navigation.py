"""Central page registry for CarePilot CN — Handles rendering of pages."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, List
import streamlit as st

# 1. Core Keys and Logic (Import from core to avoid circles)
from app.ui.page_keys import (
    PAGE_HOME, PAGE_CHAT, PAGE_MEDS, PAGE_REPORTS, PAGE_SETTINGS,
    PAGE_TIMELINE, PAGE_WORKFLOWS, PAGE_PATIENTS, DEFAULT_PAGE,
    ensure_valid_page, go_to_page
)

# 2. Dependency: Main Pages (This causes navigation -> pages)
from app.ui.pages.chat import page_chat
from app.ui.pages.dashboard import page_dashboard
from app.ui.pages.medications import page_medications
from app.ui.pages.reports import page_reports
from app.ui.pages.timeline import page_timeline
from app.ui.pages.workflows import page_workflows

@dataclass(frozen=True)
class PageDef:
    key: str
    label: str
    render: Callable[[], None]
    is_primary: bool = True
    is_placeholder: bool = False

def _placeholder_page(title: str, description: str):
    def _render():
        st.subheader(title)
        st.info(description)
    return _render

# Central Configuration for Pages
# Components should NOT import this to avoid circles
PAGE_REGISTRY: Dict[str, PageDef] = {
    PAGE_HOME: PageDef(PAGE_HOME, "🏠 今日旅程", page_dashboard, True),
    PAGE_CHAT: PageDef(PAGE_CHAT, "💬 助手中心", page_chat, True),
    PAGE_MEDS: PageDef(PAGE_MEDS, "💊 用药管理", page_medications, True),
    PAGE_TIMELINE: PageDef(PAGE_TIMELINE, "📅 健康旅程", page_timeline, False),
    PAGE_REPORTS: PageDef(
        PAGE_REPORTS, 
        "📋 健康报告", 
        _placeholder_page("📋 健康报告", "该模块正在稳定化中，演示版本暂未开放。"), 
        False, 
        True
    ),
    PAGE_WORKFLOWS: PageDef(
        PAGE_WORKFLOWS,
        "🔄 自动化流程",
        _placeholder_page("🔄 自动化流程", "正在优化 AI 自动化闭环，敬请期待。"),
        False,
        True
    ),
}

PRIMARY_PAGE_KEYS = [k for k, v in PAGE_REGISTRY.items() if v.is_primary]
SECONDARY_PAGE_KEYS = [k for k, v in PAGE_REGISTRY.items() if not v.is_primary]
