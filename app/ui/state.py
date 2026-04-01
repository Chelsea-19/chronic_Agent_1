"""app.ui.state — Centralized session_state initialization."""
import streamlit as st

from app.ui.navigation import DEFAULT_PAGE


def init_session_state():
    """Initialize all session state keys with safe defaults."""
    defaults = {
        "current_page": DEFAULT_PAGE,
        "active_patient_id": 1,
        "patient_name": "用户",
        "chat_messages": [],
        "chat_input_val": "",
        "chat_loaded": False,
        "today_journey": None,
        "selected_task_id": None,
        "last_completed_action": None,
        "db_initialized": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
