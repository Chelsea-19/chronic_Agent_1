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
    # Use the styled header from theme.py
    st.markdown('<div class="section-header">📅 健康旅程时间线</div>', unsafe_allow_html=True)
    st.caption("查看您的长期健康轨迹以及 CarePilot 的智能分析。")
    st.markdown("<br>", unsafe_allow_html=True)

    pid = st.session_state.active_patient_id
    if not pid:
        st.warning("👋 请先在侧边栏选择一名患者以查看其健康记录。")
        return

    # ── Display Controls ───────────────────────────────
    with st.container():
        limit = st.select_slider("显示条数", options=[20, 50, 100], value=50)

    st.markdown("<br>", unsafe_allow_html=True)
    db = get_db()
    try:
        repo = TimelineRepository(db, pid)
        items = repo.build(limit=limit)

        if not items:
            st.info("📅 暂无历史记录。建议从「助手中心」开始您的第一条记录。")
            return

        # ── Timeline Rendering ──────────────────────────
        for idx, item in enumerate(items):
            icon = EVENT_ICONS.get(item["item_type"], "📌")
            occurred = item["occurred_at"]
            time_str = occurred.strftime("%Y-%m-%d %H:%M")
            
            # Risk detection - using consistent logic but better UI
            is_risk = any(kw in item["detail"].lower() or kw in item["title"].lower() for kw in ["风险", "高", "异常", "警告", "risk", "high"])
            
            # Use of st.container(border=True) which was styled in theme.py
            with st.container(border=is_risk):
                if is_risk:
                    st.markdown(f'<div style="color: #dc2626; font-weight: 800; font-size: 0.75rem; margin-bottom: 0.4rem;">⚠️ 风险预警</div>', unsafe_allow_html=True)
                
                col_i, col_c, col_a = st.columns([0.15, 0.65, 0.2])
                
                with col_i:
                    st.markdown(f"<h2 style='margin:0; text-align:center;'>{icon}</h2>", unsafe_allow_html=True)
                
                with col_c:
                    st.markdown(f"**{item['title']}**")
                    # Use standard markdown or safe colors
                    st.markdown(f"<div>{item['detail']}</div>", unsafe_allow_html=True)
                    st.caption(f"发生于 {time_str}")
                    
                    if is_risk:
                        with st.expander("🔍 AI 智能解读"):
                            st.info("基于您的历史病史，该事件可能具有潜在风险。助手建议您关注此趋势，并在下次就诊时向医生反馈相关症状。")

                with col_a:
                    if st.button("问助手", key=f"ask_ev_{idx}", use_container_width=True):
                        st.session_state.chat_input_val = f"帮我分析一下 '{item['title']}' ({time_str}) 发生的背景和建议。"
                        st.session_state.current_page = "chat"
                        st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption(f"🔍 已成功同步并展示最近 {len(items)} 条健康状态动态")

    except Exception as e:
        st.error(f"❌ 加载历史数据时发生错误: {e}")
    finally:
        db.close()
