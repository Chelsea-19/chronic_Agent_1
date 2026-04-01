"""Medications page with guardrails and user-friendly fallback."""
import streamlit as st

from app.core.database import get_db
from app.features.medications.service import MedicationService
from app.ui.errors import log_exception, show_user_error


def page_medications():
    st.subheader("💊 用药管理")
    st.caption("如果你刚吃完药，可以在这里快速确认。")

    pid = st.session_state.get("active_patient_id")
    if not pid:
        st.info("请先在侧边栏选择患者。")
        return

    tab_list, tab_add = st.tabs(["当前用药", "新增记录"])

    with tab_list:
        db = get_db()
        try:
            meds = MedicationService(db, pid).list_active()
            if not meds:
                st.info("还没有用药记录，先从第一条开始。")
            for med in meds:
                with st.container(border=True):
                    st.markdown(f"**{med.medicine_name}**")
                    st.caption(f"剂量：{med.dose or '未填写'} · 时间：{med.schedule or '未填写'}")
                    if med.notes:
                        st.write(f"备注：{med.notes}")
                    if st.button("标记停用", key=f"deactivate_{med.id}"):
                        try:
                            MedicationService(db, pid).deactivate(med.id)
                            st.success(f"已停用 {med.medicine_name}")
                            st.rerun()
                        except Exception as exc:
                            log_exception("med_deactivate_failed", exc)
                            show_user_error("停用失败，请稍后重试。")
        except Exception as exc:
            log_exception("med_list_failed", exc)
            show_user_error("当前无法读取用药数据，请稍后重试。")
        finally:
            db.close()

    with tab_add:
        with st.form("add_med_form", clear_on_submit=True):
            medicine_name = st.text_input("药物名称 *", placeholder="例如：二甲双胍")
            c1, c2 = st.columns(2)
            with c1:
                dose = st.text_input("剂量", placeholder="例如：500mg")
            with c2:
                schedule = st.selectbox("服药时间", ["早餐前", "早餐后", "午餐前", "午餐后", "晚餐前", "晚餐后", "睡前"])
            notes = st.text_input("备注", placeholder="可选")
            submitted = st.form_submit_button("添加药物", use_container_width=True, type="primary")

        if submitted:
            if not medicine_name.strip():
                st.warning("请填写药物名称后再提交。")
            else:
                db = get_db()
                try:
                    MedicationService(db, pid).create(
                        medicine_name=medicine_name.strip(),
                        dose=dose.strip(),
                        schedule=schedule,
                        notes=notes.strip(),
                    )
                    st.success(f"已添加 {medicine_name.strip()}")
                    st.rerun()
                except Exception as exc:
                    log_exception("med_create_failed", exc)
                    show_user_error("添加失败，请稍后重试。")
                finally:
                    db.close()
