"""Stable companion chat page with structured guidance and error resilience."""
import streamlit as st

from app.core.database import get_db
from app.features.companion.chat_service import CompanionChatService
from app.services.repositories import ChatRepository
from app.ui.components.action_cards import render_suggestion_chip
from app.ui.errors import log_exception
# Fix: Import from page_keys instead of navigation to avoid circular dependency
from app.ui.page_keys import PAGE_HOME, PAGE_MEDS, PAGE_REPORTS, ensure_valid_page


def _render_assistant_result(result: dict):
    """Auxiliary to render structured assistant response (cards, suggestions)."""
    cards = result.get("cards", []) or []
    actions = result.get("actions", []) or []

    # 1. Action Cards
    for card in cards:
        with st.container(border=True):
            st.markdown(f"**{card.get('title', '💡 智能建议')}**")
            content = card.get("content") or ""
            if content:
                st.write(content)
            items = card.get("items", []) or []
            if items:
                st.write("；".join(items))

    # 2. Suggested Actions (Quick Buttons)
    if actions:
        st.markdown("<br>", unsafe_allow_html=True)
        cols = st.columns(min(len(actions), 3))
        for idx, act in enumerate(actions[:3]):
            with cols[idx]:
                payload = act.get("payload", {})
                # Ensure the page key in payload is valid
                if "page" in payload:
                    payload["page"] = ensure_valid_page(payload["page"])
                
                render_suggestion_chip(
                    label=act.get("label", "下一步"),
                    action_type=act.get("action_type", "link"),
                    payload=payload,
                    key=f"chat_action_{idx}",
                )


def page_chat():
    """Renders the AI Assistant center."""
    
    # ── Safety Check: Patient ──────────────────────────
    pid = st.session_state.get("active_patient_id")
    if not pid:
        st.info("👋 欢迎来到助手中心！请在左侧栏选择一名患者后再开始对话。")
        return

    # ── Header ─────────────────────────────────────────
    st.markdown('<div class="section-header">💬 智能助手中心</div>', unsafe_allow_html=True)
    st.caption("您可以提问：用药计划、饮食建议、健康数据记录、最近动态分析。")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Initialize/Load History ───────────────────────
    if not st.session_state.get("chat_loaded"):
        db = get_db()
        try:
            repo = ChatRepository(db, pid)
            messages = repo.recent(limit=20)
            # Standardize message objects
            st.session_state.chat_messages = [
                {"role": m.role, "content": m.content, "result": {}} 
                for m in messages
            ]
        except Exception as exc:
            log_exception("chat_history_load_failed", exc)
            st.session_state.chat_messages = []
            st.warning("⚠️ 历史对话读取失败，已为您开启新窗口。")
        finally:
            st.session_state.chat_loaded = True
            db.close()

    # ── Chat Dialogue Display ──────────────────────────
    for msg in st.session_state.get("chat_messages", []):
        role = msg.get("role", "assistant")
        with st.chat_message(role):
            st.markdown(msg.get("content", ""))
            if role == "assistant" and msg.get("result"):
                _render_assistant_result(msg.get("result"))

    # ── Input Handling ─────────────────────────────────
    prompt = st.chat_input("输入例如：帮我查一下早餐后的血糖。")
    
    # Check if a prompt was pre-filled (from a chip click)
    if st.session_state.get("chat_input_val"):
        prompt = st.session_state.chat_input_val
        st.session_state.chat_input_val = ""  # Clear after use

    if prompt:
        # User message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Assistant thinking
        with st.chat_message("assistant"):
            with st.spinner("CarePilot 正在分析您的健康数据..."):
                db = get_db()
                try:
                    chat_service = CompanionChatService(db, pid)
                    result = chat_service.handle_message(prompt) or {}
                    
                    reply = result.get("reply", "我已收到，正在为您整理建议。")
                    
                    # Ensure basic structure if missing
                    if "actions" not in result:
                        result["actions"] = [
                            {"label": "返回今日旅程", "payload": {"page": PAGE_HOME}},
                            {"label": "记录用药情况", "payload": {"page": PAGE_MEDS}},
                        ]
                except Exception as exc:
                    log_exception("chat_service_failed", exc)
                    reply = "⚠️ 抱歉，智能服务暂时不可达。请尝试重新描述或点击下方快捷链接。"
                    result = {
                        "reply": reply,
                        "actions": [{"label": "查看今日状态", "payload": {"page": PAGE_HOME}}],
                    }
                finally:
                    db.close()

            st.markdown(reply)
            _render_assistant_result(result)
            
            # Persist to session
            st.session_state.chat_messages.append({
                "role": "assistant", 
                "content": reply, 
                "result": result
            })

    # ── Quick Suggestions Footer ──────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("**您可以尝试搜索：**")
    c1, c2, c3 = st.columns(3)
    with c1:
        render_suggestion_chip("我的用药计划", "prompt", {"prompt": "我想看一下我今天的详细用药计划。"}, "quick_q1")
    with c2:
        render_suggestion_chip("血糖异常分析", "prompt", {"prompt": "我最近的血糖有波动吗？帮我分析下原因。"}, "quick_q2")
    with c3:
        render_suggestion_chip("下一步怎么做", "link", {"page": PAGE_HOME}, "quick_q3")
