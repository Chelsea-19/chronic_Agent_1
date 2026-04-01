import streamlit as st

from app.ui.navigation import PAGE_CHAT, PAGE_HOME, ensure_valid_page, go_to_page


def render_task_card(task_id: str, title: str, reason: str, urgency: str, effort: str, action_type: str, action_payload: dict):
    urgency_label = {"high": "高优先", "medium": "中优先", "low": "常规"}.get(urgency, "任务")

    with st.container(border=True):
        st.caption(f"{urgency_label} · 预计耗时 {effort}")
        st.markdown(f"**{title}**")
        st.write(reason)

        if st.button("前往执行", key=f"btn_task_{task_id}", use_container_width=True):
            if action_type == "link":
                target_page = ensure_valid_page(action_payload.get("page", PAGE_HOME))
                go_to_page(target_page)


def render_suggestion_chip(label: str, action_type: str, payload: dict, key: str):
    if st.button(label, key=f"chip_{key}", use_container_width=True):
        if action_type == "link":
            target_page = ensure_valid_page(payload.get("page", PAGE_HOME))
            go_to_page(target_page)
        elif action_type == "prompt":
            st.session_state.chat_input_val = payload.get("prompt", "")
            go_to_page(PAGE_CHAT)
