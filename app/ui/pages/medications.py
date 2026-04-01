"""Medications page with clear medical tracking and robust fallback."""
import streamlit as st

from app.core.database import get_db
from app.features.medications.service import MedicationService
from app.ui.errors import log_exception, show_user_error


def page_medications():
    """Renders the Medication Management page."""
    
    # ── Header ─────────────────────────────────────────
    st.markdown('<div class="section-header">💊 智能用药管理</div>', unsafe_allow_html=True)
    st.caption("维护一份准确的用药清单是疾病管理的关键。")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Safety Check: Patient ──────────────────────────
    pid = st.session_state.get("active_patient_id")
    if not pid:
        st.info("👋 请在左侧栏选择一名患者后再查看其用药计划。")
        return

    # ── Main Tabs ──────────────────────────────────────
    tab_list, tab_add = st.tabs(["📋 当前服用的药物", "➕ 添加新药物"])

    # ── Tab 1: Medication List ─────────────────────────
    with tab_list:
        db = get_db()
        try:
            med_service = MedicationService(db, pid)
            meds = med_service.list_active()
            
            if not meds:
                st.info("📅 暂无正在服用的药物情况。点击「添加新药物」开始记录。")
            else:
                for med in meds:
                    # Using container for better visual separation
                    with st.container(border=True):
                        c1, c2 = st.columns([0.8, 0.2])
                        with c1:
                            st.markdown(f"**{med.medicine_name}**")
                            st.caption(f"💊 剂量：{med.dose or '默认剂量'} · 🕒 计划：{med.schedule or '按需服用'}")
                            if med.notes:
                                st.write(f"备注：{med.notes}")
                        with c2:
                            if st.button("标记停用", key=f"deactivate_{med.id}", use_container_width=True):
                                try:
                                    med_service.deactivate(med.id)
                                    st.success(f"已更新：{med.medicine_name} 已停用。")
                                    st.rerun()
                                except Exception as exc:
                                    log_exception("med_deactivate_failed", exc)
                                    show_user_error("❌ 无法停用，请稍后刷新重试。")
        except Exception as exc:
            log_exception("med_list_failed", exc)
            show_user_error("⚠️ 药物列表加载失败。")
        finally:
            db.close()

    # ── Tab 2: Add Medication ──────────────────────────
    with tab_add:
        st.markdown("##### 填写用药概览")
        with st.form("add_med_form", clear_on_submit=True):
            medicine_name = st.text_input("药物通用名称 *", placeholder="例如：盐酸二甲双胍片")
            
            col_d, col_s = st.columns(2)
            with col_d:
                dose = st.text_input("剂量/规格", placeholder="例如：500mg/片")
            with col_s:
                schedule = st.selectbox(
                    "服药时间点", 
                    ["早餐前", "早餐后", "午餐前", "午餐后", "晚餐前", "晚餐后", "睡前", "空腹", "按需"]
                )
            
            notes = st.text_area("医生备注/自我提醒", placeholder="例如：饭后半小时服用，避免饮酒。")
            submitted = st.form_submit_button("✅ 确认添加", use_container_width=True, type="primary")

        if submitted:
            # Basic validation
            if not medicine_name.strip():
                st.warning("⚠️ 请输入药物名称后再确认添加。")
            else:
                db = get_db()
                try:
                    med_service = MedicationService(db, pid)
                    med_service.create(
                        medicine_name=medicine_name.strip(),
                        dose=dose.strip() if dose else None,
                        schedule=schedule,
                        notes=notes.strip() if notes else None,
                    )
                    st.success(f"🎊 成功！已将 「{medicine_name.strip()}」 加入当前用药清单。")
                    st.rerun()
                except Exception as exc:
                    log_exception("med_create_failed", exc)
                    show_user_error("❌ 添加失败，请联系管理员。")
                finally:
                    db.close()
