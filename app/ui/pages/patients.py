"""
Patients page — Patient profile management and follow-up scheduling.
"""
import streamlit as st
from datetime import date, timedelta

from app.core.database import get_db
from app.features.patients.service import PatientService


def page_patients():
    st.markdown('<div class="section-header">👤 患者管理</div>', unsafe_allow_html=True)

    tab_list, tab_add, tab_followup = st.tabs(["📋 患者列表", "➕ 新建患者", "📅 复诊管理"])

    # ── Tab 1: Patient List ──────────────────────────────
    with tab_list:
        st.subheader("患者档案")
        db = get_db()
        try:
            patients = PatientService(db).list_patients()
            if patients:
                for p in patients:
                    active = p.id == st.session_state.active_patient_id
                    border = "border-left: 3px solid #4F8BF9;" if active else ""
                    with st.container():
                        st.markdown(
                            f'<div style="padding: 0.5rem; {border}">',
                            unsafe_allow_html=True,
                        )
                        cols = st.columns([1, 2, 2, 2, 1])
                        with cols[0]:
                            st.markdown(f"**ID {p.id}**")
                        with cols[1]:
                            st.markdown(f"👤 {p.name}")
                        with cols[2]:
                            st.caption(f"性别: {p.gender or '—'} | 年龄: {p.age or '—'}")
                        with cols[3]:
                            st.caption(f"📝 {p.diagnosis_summary}")
                        with cols[4]:
                            if not active:
                                if st.button("切换", key=f"switch_{p.id}"):
                                    st.session_state.active_patient_id = p.id
                                    st.session_state.chat_loaded = False
                                    st.toast(f"已切换到 {p.name}")
                                    st.rerun()
                            else:
                                st.markdown(
                                    '<span class="status-badge status-info">当前</span>',
                                    unsafe_allow_html=True,
                                )
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.divider()
            else:
                st.info("暂无患者记录")
        finally:
            db.close()

    # ── Tab 2: Add Patient ───────────────────────────────
    with tab_add:
        st.subheader("创建新患者")
        with st.form("add_patient_form", clear_on_submit=True):
            name = st.text_input("姓名 *", placeholder="请输入患者姓名")
            col1, col2 = st.columns(2)
            with col1:
                gender = st.selectbox("性别", ["男", "女", "未知"], index=2)
            with col2:
                age = st.number_input("年龄", min_value=0, max_value=150, value=60)
            diagnosis = st.text_input("诊断摘要", value="2型糖尿病合并高血压")
            phone = st.text_input("联系电话", placeholder="可选")
            submitted = st.form_submit_button("✅ 创建患者", use_container_width=True, type="primary")

        if submitted:
            if not name:
                st.error("请输入患者姓名")
            else:
                db = get_db()
                try:
                    PatientService(db).create_patient(
                        name=name, gender=gender, age=age,
                        diagnosis_summary=diagnosis, phone=phone,
                    )
                    st.success(f"✅ 患者「{name}」已创建！")
                    st.rerun()
                except Exception as e:
                    st.error(f"创建失败: {e}")
                finally:
                    db.close()

    # ── Tab 3: Follow-ups ────────────────────────────────
    with tab_followup:
        pid = st.session_state.active_patient_id
        st.subheader(f"复诊管理 (患者 ID: {pid})")

        # Add follow-up
        with st.form("followup_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                scheduled_for = st.date_input("复诊日期", value=date.today() + timedelta(days=7))
            with col2:
                purpose = st.text_input("目的", value="复诊")
            notes = st.text_input("备注", placeholder="可选备注")
            submitted_fu = st.form_submit_button("📅 添加复诊", use_container_width=True)

        if submitted_fu:
            db = get_db()
            try:
                PatientService(db).create_followup(pid, scheduled_for, purpose, notes)
                st.success("✅ 复诊已添加")
                st.rerun()
            except Exception as e:
                st.error(f"添加失败: {e}")
            finally:
                db.close()

        # List follow-ups
        st.divider()
        db = get_db()
        try:
            followups = PatientService(db).list_followups(pid)
            if followups:
                for fu in followups:
                    status_class = "status-info" if fu.status == "planned" else "status-success"
                    st.markdown(
                        f"📅 **{fu.scheduled_for}** | {fu.purpose} | "
                        f'<span class="status-badge {status_class}">{fu.status}</span> '
                        f"| {fu.notes or '—'}",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("暂无复诊记录")
        finally:
            db.close()
