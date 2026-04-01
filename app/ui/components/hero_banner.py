import streamlit as st

from app.ui.navigation import PAGE_HOME, ensure_valid_page, go_to_page


def render_hero_banner(greeting: str, message: str, primary_cta: dict = None):
    patient_name = st.session_state.get("patient_name", "用户")

    with st.container(border=True):
        st.subheader(f"{greeting}，{patient_name}")
        st.write(message)

        if primary_cta and st.button(f"👉 {primary_cta.get('label', '继续')}", key="hero_cta", type="primary"):
            payload = primary_cta.get("payload", {})
            go_to_page(ensure_valid_page(payload.get("page", PAGE_HOME)))
