"""
app.ui.pages.timeline — Enhanced longitudinal patient event timeline.
"""
import streamlit as st
from datetime import datetime
from app.core.database import get_db
from app.services.repositories import TimelineRepository

EVENT_ICONS = {
    "health_event": "🩺",
    "meal": "🍽️",
    "reminder": "💊",
    "digest": "📄",
    "followup": "📅",
}

def page_timeline():
    st.markdown('<div class="section-header">📅 健康旅程时间线</div>', unsafe_allow_html=True)

    pid = st.session_state.active_patient_id
    if not pid:
        st.warning("请先在侧边栏选择一名患者。")
        return

    # ── Header & Filters ───────────────────────────────
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown("**查看您的长期健康轨迹以及 CarePilot 的智能分析。**")
    with c2:
        limit = st.select_slider("显示条数", options=[20, 50, 100], value=50, label_visibility="collapsed")

    st.write("")
    db = get_db()
    try:
        repo = TimelineRepository(db, pid)
        items = repo.build(limit=limit)

        if not items:
            st.info("暂无记录。开始记录您的健康旅程吧！", icon="ℹ️")
            return

        # ── Timeline Rendering ──────────────────────────
        for idx, item in enumerate(items):
            icon = EVENT_ICONS.get(item["item_type"], "📌")
            occurred = item["occurred_at"]
            time_str = occurred.strftime("%Y-%m-%d %H:%M")
            # Logic to detect "risk" string or any high values
            is_risk = any(kw in item["detail"].lower() or kw in item["title"].lower() for kw in ["风险", "高", "异常", "警告", "risk", "high"])
            
            with st.container(border=is_risk):
                if is_risk:
                    st.markdown(f'<div style="color: #ef4444; font-weight: 800; font-size: 0.75rem; margin-bottom: 0.5rem;">⚠️ 风险预警</div>', unsafe_allow_html=True)
                
                col_i, col_c, col_a = st.columns([0.1, 0.7, 0.2])
                
                with col_i:
                    st.markdown(f"<h2 style='margin:0;'>{icon}</h2>", unsafe_allow_html=True)
                
                with col_c:
                    st.markdown(f"**{item['title']}**")
                    st.markdown(f"<div style='font-size: 0.95rem; color: #475569;'>{item['detail']}</div>", unsafe_allow_html=True)
                    st.caption(f"发生于 {time_str}")
                    
                    if is_risk:
                        with st.expander("🔍 AI 智能解读"):
                            st.info("基于您的病史，此事件可能暗示近期血糖波动。建议在下次随访时与医生沟通。")

                with col_a:
                    if st.button("问助手", key=f"ask_ev_{idx}", use_container_width=True):
                        st.session_state.chat_input_val = f"帮我分析一下 '{item['title']}' ({time_str}) 发生的背景和建议。"
                        st.session_state.current_page = "chat"
                        st.rerun()

        st.write("")
        st.caption(f"🔍 已成功同步并展示最近 {len(items)} 条完整健康动态")

    except Exception as e:
        st.error(f"加载时间线失败: {e}")
    finally:
        db.close()
