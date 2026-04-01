"""Today journey page focused on stable MVP flow with proactive care guidance."""
import streamlit as st

from app.core.database import get_db
from app.features.journey.service import JourneyService
from app.services.repositories import TimelineRepository
from app.ui.components.action_cards import render_suggestion_chip, render_task_card
from app.ui.components.hero_banner import render_hero_banner
from app.ui.components.progress_widgets import render_progress_widget
from app.ui.errors import log_exception, show_user_error


def page_dashboard():
    """Renders the main Journey (Dashboard) page."""
    
    # ── Safety Check 1: Patient Selection ────────────────
    pid = st.session_state.get("active_patient_id")
    if not pid:
        st.info("👋 您好！请先在侧边栏选择一名患者，开启其专属健康旅程。")
        return

    # ── Safety Check 2: Error Handling ──────────────────
    db = get_db()
    try:
        # Load journey state through service
        journey_service = JourneyService(db, pid)
        journey_state = journey_service.get_state()

        # Update Session State with Greeting and message (optional)
        primary_cta = None
        if hasattr(journey_state, "suggested_next_action") and journey_state.suggested_next_action:
            action = journey_state.suggested_next_action
            primary_cta = {"label": action.label, "payload": action.payload}

        # ── Header 1: Hero Section ──────────────────────────
        render_hero_banner(
            getattr(journey_state, "greeting", f"您好，{st.session_state.patient_name}"), 
            getattr(journey_state, "hero_message", "今天要开始新的健康记录吗？助理已为您准备好建议。"), 
            primary_cta
        )

        st.markdown("<br>", unsafe_allow_html=True)
        
        # ── Main Content Columns ────────────────────────────
        col_main, col_side = st.columns([2.5, 1], gap="large")

        with col_main:
            st.markdown(f'<div class="section-header">🚩 今日关键任务</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            tasks = getattr(journey_state, "tasks", []) or []
            if not tasks:
                # Fallback Empty State
                st.info("📅 今天暂无待办任务。建议通过「助手中心」记录血糖或同步用药情况。")
                render_suggestion_chip(
                    "前往助手中心交流", 
                    "link", 
                    {"page": "chat"}, 
                    "home_empty_chat"
                )
            else:
                # Limit shown tasks to avoid clutter
                for task in tasks[:3]:
                    render_task_card(
                        task.id, 
                        task.title, 
                        task.reason, 
                        getattr(task, "urgency", "medium"), 
                        getattr(task, "effort", "5m"), 
                        getattr(task, "action_type", "link"), 
                        getattr(task, "action_payload", {})
                    )

        with col_side:
            # ── Sidebar Metric Widgets ──────────────────────
            st.markdown(f'<div class="section-header">📊 达成情况</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            completion = getattr(journey_state, "completion", []) or []
            if not completion:
                st.caption("暂无实时达成指标。")
            else:
                for stat in completion:
                    render_progress_widget(stat.category, stat.completed, stat.total, stat.percentage)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f'<div class="section-header">🕒 最新动态</div>', unsafe_allow_html=True)
            
            # Load timeline items as fallback/overview
            recent_events = TimelineRepository(db, pid).build(limit=3) or []
            if not recent_events:
                st.caption("还没有最近记录。")
            else:
                for idx, ev in enumerate(recent_events):
                    with st.container():
                        st.markdown(f"**{ev['title']}**")
                        st.caption(f"{ev['occurred_at'].strftime('%H:%M')} · {ev.get('detail', '')}")
                        if idx < len(recent_events) - 1:
                            st.divider()

    except Exception as exc:
        log_exception("dashboard_load_failed", exc)
        show_user_error("今日旅程系统正在维护，暂时无法读取数据，请刷新或稍后再试。")
    finally:
        db.close()
