"""Sidebar navigation and patient selector for CarePilot CN."""
import streamlit as st

from app.core.config import get_settings
from app.core.database import get_db
from app.services.repositories import PatientRepository
from app.ui.navigation import (
    PAGE_REGISTRY,
    PRIMARY_PAGE_KEYS,
    SECONDARY_PAGE_KEYS,
    ensure_valid_page,
)


def render_sidebar() -> str:
    """Render the sidebar and return the current selected stable page key."""
    with st.sidebar:
        st.markdown(
            f'<div style="font-size: 1.5rem; font-weight: 800; color: #2563eb; margin-bottom: 0.5rem;">🏥 CarePilot CN</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-size: 0.85rem; color: #64748b; margin-bottom: 1.5rem;">慢性病 AI 管理助手 · 演示版</div>',
            unsafe_allow_html=True,
        )

        db = get_db()
        try:
            patients = PatientRepository(db).list_all()
            if patients:
                # Use ID as key, Name as Label
                patient_options = {f"👤 {p.name}": p.id for p in patients}
                labels = list(patient_options.keys())
                
                # Check current ID in state
                curr_pid = st.session_state.get("active_patient_id")
                idx = 0
                if curr_pid:
                    for i, (l, pid) in enumerate(patient_options.items()):
                        if pid == curr_pid:
                            idx = i
                            break
                            
                selected_label = st.selectbox(
                    "切换管理患者", 
                    options=labels, 
                    index=idx, 
                    help="选择一个患者启动其慢病管理视图。"
                )
                
                if selected_label:
                    new_pid = patient_options[selected_label]
                    if new_pid != st.session_state.active_patient_id:
                        st.session_state.active_patient_id = new_pid
                        st.session_state.patient_name = selected_label.replace("👤 ", "")
                        st.rerun()
            else:
                st.warning("⚠️ 暂无患者数据，请联系管理员或切换到演示模式。")
                st.session_state.active_patient_id = None
        except Exception:
            st.error("❌ 数据库连接异常，请检查本地环境。")
        finally:
            db.close()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**主导航**")

        # 1. Primary Navigation using radio for stability
        primary_labels = [PAGE_REGISTRY[k].label for k in PRIMARY_PAGE_KEYS]
        current_page = ensure_valid_page(st.session_state.get("current_page"))
        
        default_idx = 0
        if current_page in PRIMARY_PAGE_KEYS:
            current_label = PAGE_REGISTRY[current_page].label
            if current_label in primary_labels:
                default_idx = primary_labels.index(current_label)

        selected_label = st.radio(
            "Navigation",
            primary_labels,
            index=default_idx,
            label_visibility="collapsed"
        )
        
        # Sync back from label to key
        for k in PRIMARY_PAGE_KEYS:
            if PAGE_REGISTRY[k].label == selected_label:
                if st.session_state.current_page != k:
                    st.session_state.current_page = k
                    st.rerun()
                break

        # 2. Secondary Navigation in Expander
        with st.expander("🔍 更多管理功能", expanded=False):
            for k in SECONDARY_PAGE_KEYS:
                pdef = PAGE_REGISTRY[k]
                if st.button(pdef.label, use_container_width=True, key=f"side_more_{k}"):
                    st.session_state.current_page = k
                    st.rerun()

        # 3. Status and Settings
        st.markdown("<div style='flex-grow: 1'></div>", unsafe_allow_html=True)
        st.divider()
        settings = get_settings()
        llm_status = "🟢 模型就绪" if settings.llm_configured else "🟡 规则驱动"
        st.caption(f"系统状态：{llm_status}")
        st.caption(f"当前版本：v1.0.2-MVP")

    return st.session_state.current_page
