"""Stable companion chat page with graceful degradation."""
import streamlit as st

from app.core.database import get_db
from app.features.companion.chat_service import CompanionChatService
from app.services.repositories import ChatRepository
from app.ui.components.action_cards import render_suggestion_chip
from app.ui.errors import log_exception
from app.ui.navigation import PAGE_HOME, PAGE_MEDS, PAGE_REPORTS, ensure_valid_page


def _render_assistant_result(result: dict):
    cards = result.get("cards", []) or []
    actions = result.get("actions", []) or []

    for card in cards:
        with st.container(border=True):
            st.markdown(f"**{card.get('title', '信息卡片')}**")
            content = card.get("content") or ""
            if content:
                st.write(content)
            items = card.get("items", []) or []
            if items:
                st.write("；".join(items))

    if actions:
        cols = st.columns(min(len(actions), 3))
        for idx, act in enumerate(actions[:3]):
            with cols[idx]:
                payload = act.get("payload", {})
                if "page" in payload:
                    payload["page"] = ensure_valid_page(payload["page"])
                render_suggestion_chip(
                    label=act.get("label", "下一步"),
                    action_type=act.get("action_type", "link"),
                    payload=payload,
                    key=f"chat_action_{idx}",
                )


def page_chat():
    pid = st.session_state.get("active_patient_id")
    if not pid:
        st.info("请先在侧边栏选择患者。")
        return

    st.subheader("💬 助手中心")
    st.caption("可以询问记录、用药、饮食与下一步建议。")

    if not st.session_state.get("chat_loaded"):
        db = get_db()
        try:
            messages = ChatRepository(db, pid).recent(limit=50)
            st.session_state.chat_messages = [{"role": m.role, "content": m.content, "result": {}} for m in messages]
        except Exception as exc:
            log_exception("chat_history_load_failed", exc)
            st.session_state.chat_messages = []
            st.warning("历史消息暂不可用，您可以直接开始新对话。")
        finally:
            st.session_state.chat_loaded = True
            db.close()

    for msg in st.session_state.get("chat_messages", []):
        with st.chat_message(msg.get("role", "assistant")):
            st.markdown(msg.get("content", ""))
            if msg.get("role") == "assistant":
                _render_assistant_result(msg.get("result", {}))

    prompt = st.chat_input("输入消息（例如：记录今早血糖 6.5）")
    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("CarePilot 正在整理建议..."):
                db = get_db()
                try:
                    result = CompanionChatService(db, pid).handle_message(prompt) or {}
                    reply = result.get("reply", "我已收到，建议先完成今日关键任务。")
                    result.setdefault("journey_refresh", True)
                    result.setdefault(
                        "actions",
                        [
                            {"label": "查看今日旅程", "payload": {"page": PAGE_HOME}},
                            {"label": "记录用药", "payload": {"page": PAGE_MEDS}},
                        ],
                    )
                except Exception as exc:
                    log_exception("chat_service_failed", exc)
                    reply = "当前智能服务暂时不可用，请稍后重试。"
                    result = {
                        "reply": reply,
                        "actions": [{"label": "返回今日旅程", "payload": {"page": PAGE_HOME}}],
                    }
                finally:
                    db.close()

            st.markdown(reply)
            _render_assistant_result(result)

        st.session_state.chat_messages.append({"role": "assistant", "content": reply, "result": result})

    st.markdown("### 快捷建议")
    c1, c2, c3 = st.columns(3)
    with c1:
        render_suggestion_chip("记录血糖", "prompt", {"prompt": "我要记录一次餐后血糖"}, "quick_glucose")
    with c2:
        render_suggestion_chip("用药确认", "link", {"page": PAGE_MEDS}, "quick_meds")
    with c3:
        render_suggestion_chip("查看报告（建设中）", "link", {"page": PAGE_REPORTS}, "quick_reports")
