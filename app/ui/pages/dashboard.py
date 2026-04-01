"""Today journey page focused on stable MVP flow."""
import streamlit as st

from app.core.database import get_db
from app.features.journey.service import JourneyService
from app.services.repositories import TimelineRepository
from app.ui.components.action_cards import render_suggestion_chip, render_task_card
from app.ui.components.hero_banner import render_hero_banner
from app.ui.components.progress_widgets import render_progress_widget
from app.ui.errors import log_exception, show_user_error


def page_dashboard():
    pid = st.session_state.get("active_patient_id")
    if not pid:
        st.info("请先在侧边栏选择患者，再开始今天的管理。")
        return

    db = get_db()
    try:
        journey_state = JourneyService(db, pid).get_state()

        primary_cta = None
        if getattr(journey_state, "suggested_next_action", None):
            action = journey_state.suggested_next_action
            primary_cta = {"label": action.label, "payload": action.payload}

        render_hero_banner(journey_state.greeting, journey_state.hero_message, primary_cta)

        st.markdown("### 今天先完成这 2 件事")
        col_main, col_side = st.columns([2, 1], gap="large")

        with col_main:
            tasks = getattr(journey_state, "tasks", []) or []
            if not tasks:
                st.success("今天暂无待办，建议先记录一次最新健康数据。")
                render_suggestion_chip("去助手中心记录血糖", "prompt", {"prompt": "我想记录今天的血糖"}, "home_empty")
            else:
                for task in tasks[:3]:
                    render_task_card(task.id, task.title, task.reason, task.urgency, task.effort, task.action_type, task.action_payload)

        with col_side:
            st.markdown("#### 达成情况")
            completion = getattr(journey_state, "completion", []) or []
            if not completion:
                st.caption("暂无统计数据")
            for stat in completion:
                render_progress_widget(stat.category, stat.completed, stat.total, stat.percentage)

            st.markdown("#### 最近动态")
            recent_events = TimelineRepository(db, pid).build(limit=3) or []
            if not recent_events:
                st.caption("还没有健康记录，先从第一条开始。")
            else:
                for ev in recent_events:
                    st.caption(f"{ev['occurred_at'].strftime('%H:%M')} · {ev['title']}")
                    st.write(ev.get("detail", ""))

    except Exception as exc:
        log_exception("dashboard_load_failed", exc)
        show_user_error("今日旅程暂时不可用，请稍后重试。")
    finally:
        db.close()
