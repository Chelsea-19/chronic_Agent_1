"""Sidebar navigation and patient selector."""
import streamlit as st

from app.core.config import get_settings
from app.core.database import get_db
from app.services.repositories import PatientRepository
from app.ui.navigation import (
    PAGE_REGISTRY,
    PRIMARY_PAGE_KEYS,
    SECONDARY_PAGE_KEYS,
    ensure_valid_page,
)


def render_sidebar() -> str:
    """Render the sidebar and return selected stable page key."""
    with st.sidebar:
        st.title("🏥 CarePilot CN")
        st.caption("慢病管理助手 · 演示版")
        st.divider()

        db = get_db()
        try:
            patients = PatientRepository(db).list_all()
            if patients:
                patient_options = {f"{p.name} (ID:{p.id})": p.id for p in patients}
                default_label = next(iter(patient_options.keys()))
                selected = st.selectbox("👤 当前患者", options=list(patient_options.keys()), index=0)
                selected = selected or default_label
                st.session_state.active_patient_id = patient_options[selected]
                st.session_state.patient_name = selected.split(" (")[0]
            else:
                st.warning("暂无患者数据，已进入演示模式。")
                st.session_state.active_patient_id = None
                st.session_state.patient_name = "用户"
        except Exception:
            st.warning("患者数据暂不可用，您仍可体验核心页面。")
        finally:
            db.close()

        st.divider()

        primary_options = {PAGE_REGISTRY[k].label: k for k in PRIMARY_PAGE_KEYS}
        current_page = ensure_valid_page(st.session_state.get("current_page"))
        labels = list(primary_options.keys())
        default_idx = 0
        if current_page in PRIMARY_PAGE_KEYS:
            current_label = PAGE_REGISTRY[current_page].label
            default_idx = labels.index(current_label)

        selected_label = st.radio("主导航", labels, index=default_idx, label_visibility="collapsed")
        st.session_state.current_page = primary_options[selected_label]

        with st.expander("更多模块", expanded=False):
            for page_key in SECONDARY_PAGE_KEYS:
                if st.button(PAGE_REGISTRY[page_key].label, use_container_width=True, key=f"more_{page_key}"):
                    st.session_state.current_page = page_key
                    st.rerun()

        st.divider()
        settings = get_settings()
        llm_status = "🟢 LLM" if settings.llm_configured else "🟡 RULE"
        st.caption(f"{llm_status} • {settings.llm_model}")

    return ensure_valid_page(st.session_state.get("current_page"))
