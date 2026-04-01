import streamlit as st


def render_progress_widget(category: str, completed: int, total: int, percentage: float):
    with st.container(border=False):
        st.write(f"**{category}** · {completed}/{total} 已完成")
        st.progress(max(min(percentage, 100), 0) / 100.0)
        st.caption(f"完成率 {percentage}%")
