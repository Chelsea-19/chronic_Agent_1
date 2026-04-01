"""
Meals page — Meal analysis, recording, and risk tracking.
"""
import streamlit as st
from datetime import datetime

from app.core.database import get_db
from app.features.meals.service import MealService, MealAnalyzeRequest


def page_meals():
    st.markdown('<div class="section-header">🍽️ 饮食管理</div>', unsafe_allow_html=True)

    pid = st.session_state.active_patient_id
    tab_record, tab_history, tab_summary = st.tabs(["📝 记录饮食", "📜 饮食历史", "📊 营养总结"])

    # ── Tab 1: Record Meal ───────────────────────────────
    with tab_record:
        st.subheader("记录一餐")
        with st.form("meal_form", clear_on_submit=True):
            description = st.text_area(
                "饮食内容描述",
                placeholder="例如：午饭吃了一碗红烧肉盖饭、一杯全糖奶茶",
                height=100,
            )
            col1, col2 = st.columns(2)
            with col1:
                meal_time = st.selectbox(
                    "餐次", ["auto", "早餐", "午餐", "晚餐", "加餐"],
                    index=0,
                )
            with col2:
                source = st.selectbox("来源", ["text", "photo", "voice"], index=0)

            submitted = st.form_submit_button("🔍 分析并记录", use_container_width=True, type="primary")

        if submitted and description:
            db = get_db()
            try:
                service = MealService(db, pid)
                result = service.analyze_and_record(
                    MealAnalyzeRequest(description=description, meal_time=meal_time, source=source)
                )
                analysis = result["analysis"]

                st.success("✅ 饮食已记录并分析！")

                # Risk Analysis Display
                r1, r2, r3 = st.columns(3)
                with r1:
                    tags = analysis.get("risk_tags", [])
                    if tags:
                        for tag in tags:
                            color = "🔴" if "高糖" in tag or "高盐" in tag else "🟡"
                            st.markdown(f"{color} **{tag}**")
                    else:
                        st.markdown("🟢 **低风险饮食**")
                with r2:
                    st.metric("碳水估算", f"{analysis.get('estimated_carbs', 0):.0f} g")
                with r3:
                    st.metric("钠估算", f"{analysis.get('estimated_sodium_mg', 0):.0f} mg")

                st.info(f"💡 {analysis.get('advice', '')}")
            except Exception as e:
                st.error(f"分析失败: {e}")
            finally:
                db.close()

    # ── Tab 2: History ───────────────────────────────────
    with tab_history:
        st.subheader("近期饮食记录")
        db = get_db()
        try:
            records = MealService(db, pid).list_records(limit=30)
            if records:
                for r in records:
                    with st.container():
                        cols = st.columns([1, 3, 2, 1])
                        with cols[0]:
                            st.caption(r.meal_time)
                        with cols[1]:
                            st.markdown(f"**{r.description}**")
                        with cols[2]:
                            tags = r.risk_tags or "低"
                            tag_class = "status-danger" if "高" in tags else "status-success"
                            st.markdown(
                                f'<span class="status-badge {tag_class}">{tags}</span>',
                                unsafe_allow_html=True,
                            )
                        with cols[3]:
                            st.caption(r.created_at.strftime("%m-%d %H:%M"))
                        st.divider()
            else:
                st.info("暂无饮食记录。请在「记录饮食」中添加。")
        finally:
            db.close()

    # ── Tab 3: Summary ───────────────────────────────────
    with tab_summary:
        st.subheader("营养风险总结")
        db = get_db()
        try:
            service = MealService(db, pid)
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📅 今日")
                daily = service.daily_summary()
                st.metric("记录数", daily["total_records"])
                if daily["avg_estimated_carbs"]:
                    st.metric("平均碳水", f"{daily['avg_estimated_carbs']:.0f} g")
                if daily["avg_estimated_sodium_mg"]:
                    st.metric("平均钠", f"{daily['avg_estimated_sodium_mg']:.0f} mg")
                if daily["top_risk_tags"]:
                    st.warning(f"风险: {', '.join(daily['top_risk_tags'])}")

            with col2:
                st.markdown("### 📆 本周")
                weekly = service.weekly_summary()
                st.metric("记录数", weekly["total_records"])
                if weekly["avg_estimated_carbs"]:
                    st.metric("平均碳水", f"{weekly['avg_estimated_carbs']:.0f} g")
                if weekly["avg_estimated_sodium_mg"]:
                    st.metric("平均钠", f"{weekly['avg_estimated_sodium_mg']:.0f} mg")
                if weekly["top_risk_tags"]:
                    st.warning(f"风险: {', '.join(weekly['top_risk_tags'])}")
        finally:
            db.close()
