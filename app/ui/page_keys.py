"""Stable page-key constants and core navigation logic for CarePilot CN."""
import streamlit as st

# 1. Page Constants
PAGE_HOME = "home"
PAGE_CHAT = "chat"
PAGE_MEDS = "meds"
PAGE_REPORTS = "reports"
PAGE_SETTINGS = "settings"
PAGE_TIMELINE = "timeline"
PAGE_WORKFLOWS = "workflows"
PAGE_PATIENTS = "patients"

DEFAULT_PAGE = PAGE_HOME

# 2. Key Sets for validation
VALID_PAGE_KEYS = {
    PAGE_HOME, PAGE_CHAT, PAGE_MEDS, PAGE_REPORTS, 
    PAGE_SETTINGS, PAGE_TIMELINE, PAGE_WORKFLOWS, PAGE_PATIENTS
}

# 3. Legacy Mapping
LEGACY_PAGE_MAPPING = {
    "🏠 今日旅程": PAGE_HOME,
    "💬 助手中心": PAGE_CHAT,
    "💊 用药管理": PAGE_MEDS,
    "📋 健康报告": PAGE_REPORTS,
    "智能对话": PAGE_CHAT,
    "dashboard": PAGE_HOME,
    "medication": PAGE_MEDS,
}

# 4. Core Navigation Logic (No dependencies on registry/pages)
def ensure_valid_page(page_key: str | None) -> str:
    """Robust conversion of any input to a stable page key."""
    if not page_key:
        return DEFAULT_PAGE
    
    # 1. Search in legacy mapping
    if page_key in LEGACY_PAGE_MAPPING:
        return LEGACY_PAGE_MAPPING[page_key]
        
    # 2. Search in valid keys
    if page_key in VALID_PAGE_KEYS:
        return page_key
        
    # Default to home
    return DEFAULT_PAGE

def go_to_page(page_key: str):
    """Safely switch the current page and trigger rerun."""
    st.session_state.current_page = ensure_valid_page(page_key)
    st.rerun()
