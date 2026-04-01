"""Central page registry and navigation helpers for stable routing keys."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, List
import streamlit as st

from app.ui.page_keys import (
    PAGE_HOME, PAGE_CHAT, PAGE_MEDS, PAGE_REPORTS, PAGE_SETTINGS,
    PAGE_TIMELINE, PAGE_WORKFLOWS, PAGE_PATIENTS, DEFAULT_PAGE,
    LEGACY_PAGE_MAPPING
)

# Import mandatory MVP pages
from app.ui.pages.chat import page_chat
from app.ui.pages.dashboard import page_dashboard
from app.ui.pages.medications import page_medications

# Import optional/secondary pages
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
PAGE_REGISTRY: Dict[str, PageDef] = {
    PAGE_HOME: PageDef(PAGE_HOME, "🏠 今日旅程", page_dashboard, True),
    PAGE_CHAT: PageDef(PAGE_CHAT, "💬 助手中心", page_chat, True),
    PAGE_MEDS: PageDef(PAGE_MEDS, "💊 用药管理", page_medications, True),
    
    # Secondary Pages - High Quality but not core MVP
    PAGE_TIMELINE: PageDef(PAGE_TIMELINE, "📅 健康旅程", page_timeline, False),
    
    # Placeholder Pages - For modules that need stabilization
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

def ensure_valid_page(page_key: str | None) -> str:
    """Robust conversion of any input (label, old key, etc) to a stable page key."""
    if not page_key:
        return DEFAULT_PAGE
    
    # 1. Search in legacy mapping
    if page_key in LEGACY_PAGE_MAPPING:
        return LEGACY_PAGE_MAPPING[page_key]
        
    # 2. Search in registry keys
    if page_key in PAGE_REGISTRY:
        return page_key
        
    # 3. Search in registry labels (as a last resort fallback)
    for k, v in PAGE_REGISTRY.items():
        if v.label == page_key:
            return k
            
    # Default to home
    return DEFAULT_PAGE

def go_to_page(page_key: str):
    """Safely switch the current page and trigger rerun."""
    st.session_state.current_page = ensure_valid_page(page_key)
    st.rerun()
