"""
Reminders page — Medication reminder management.
Replaces the original background worker with on-demand generation.
"""
import streamlit as st
from datetime import date

from app.core.database import get_db
from app.features.reminders.service import ReminderService


def page_reminders():
    st.markdown('<div class="section-header">⏰ 服药提醒</div>', unsafe_allow_html=True)
    st.caption("基于当前用药计划自动生成每日服药提醒。原系统使用后台 Worker 轮询，此处改为用户按需触发。")

    pid = st.session_state.active_patient_id

    # ── Generate Reminders ───────────────────────────────
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**📅 今日日期:** {date.today().isoformat()}")
    with col2:
        if st.button("🔄 生成今日提醒", use_container_width=True, type="primary"):
            db = get_db()
            try:
                created = ReminderService(db, pid).generate_today()
                if created:
                    st.toast(f"✅ 已生成 {len(created)} 条新提醒", icon="⏰")
                else:
                    st.toast("📋 今日提醒已是最新", icon="ℹ️")
                st.rerun()
            finally:
                db.close()

    st.divider()

    # ── Today's Reminders ────────────────────────────────
    db = get_db()
    try:
        service = ReminderService(db, pid)
        reminders = service.list_today()

        if reminders:
            pending = [r for r in reminders if r.status == "pending"]
            done = [r for r in reminders if r.status == "done"]
            skipped = [r for r in reminders if r.status == "skipped"]

            # Pending
            if pending:
                st.subheader(f"⏳ 待处理 ({len(pending)})")
                for r in pending:
                    with st.container():
                        cols = st.columns([3, 2, 1, 1])
                        with cols[0]:
                            st.markdown(f"💊 **{r.medication.medicine_name}**")
                        with cols[1]:
                            st.caption(f"⏰ {r.schedule_label}")
                        with cols[2]:
                            if st.button("✅ 已服", key=f"done_{r.id}"):
                                service.update_status(r.id, "done")
                                st.rerun()
                        with cols[3]:
                            if st.button("⏭️ 跳过", key=f"skip_{r.id}"):
                                service.update_status(r.id, "skipped")
                                st.rerun()
                        st.divider()

            # Done
            if done:
                with st.expander(f"✅ 已完成 ({len(done)})", expanded=False):
                    for r in done:
                        st.markdown(
                            f'💊 {r.medication.medicine_name} · {r.schedule_label} '
                            f'<span class="status-badge status-success">已服</span>',
                            unsafe_allow_html=True,
                        )

            # Skipped
            if skipped:
                with st.expander(f"⏭️ 已跳过 ({len(skipped)})", expanded=False):
                    for r in skipped:
                        st.markdown(
                            f'💊 {r.medication.medicine_name} · {r.schedule_label} '
                            f'<span class="status-badge status-warning">跳过</span>',
                            unsafe_allow_html=True,
                        )

            # Summary metrics
            st.divider()
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("待处理", len(pending))
            with m2:
                st.metric("已完成", len(done))
            with m3:
                st.metric("已跳过", len(skipped))
        else:
            st.info("今日暂无提醒。请先添加药物并点击「生成今日提醒」。")
    finally:
        db.close()
