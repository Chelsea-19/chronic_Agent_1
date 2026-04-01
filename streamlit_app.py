"""CarePilot CN Streamlit entry point."""
import streamlit as st

st.set_page_config(
    page_title="CarePilot CN · 慢性病智能管理平台",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "CarePilot CN — AI-Powered Chronic Disease Management for Mainland China",
    },
)

from app.core.config import get_settings
from app.core.database import init_db
from app.core.theme import inject_custom_css
from app.ui.navigation import PAGE_REGISTRY, ensure_valid_page
from app.ui.sidebar import render_sidebar
from app.ui.state import init_session_state

settings = get_settings()
init_db()
init_session_state()
inject_custom_css()

selected_page = ensure_valid_page(render_sidebar())
PAGE_REGISTRY[selected_page].render()
