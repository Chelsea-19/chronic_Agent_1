"""CarePilot CN — Hero Banner component with actionable guidance."""
import streamlit as st

from app.ui.navigation import PAGE_HOME, ensure_valid_page, go_to_page


def render_hero_banner(greeting: str, message: str, primary_cta: dict = None):
    """Renders a prominent welcoming banner with an optional call-to-action."""
    patient_name = st.session_state.get("patient_name", "用户")

    # Wrap in a specialized container with extra visual weight
    with st.container(border=True):
        st.markdown(
            f'<div style="font-size: 1.5rem; font-weight: 800; color: #2563eb; margin-bottom: 0.5rem;">{greeting}，{patient_name} 👋</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-size: 1.1rem; color: #334155; line-height: 1.6; margin-bottom: 1rem;">{message}</div>',
            unsafe_allow_html=True,
        )

        if primary_cta:
            label = primary_cta.get("label", "立即开始执行")
            payload = primary_cta.get("payload", {})
            
            # Using st.button since it's already styled in theme.py
            if st.button(f"👉 {label}", key="hero_cta", type="primary", use_container_width=False):
                target = ensure_valid_page(payload.get("page", PAGE_HOME))
                # Add prompt pre-fill if detected in payload
                if payload.get("prompt"):
                    st.session_state.chat_input_val = payload["prompt"]
                go_to_page(target)
