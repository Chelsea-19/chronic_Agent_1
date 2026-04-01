"""
Workflows page — State-machine workflow execution and monitoring.
"""
import json
import streamlit as st

from app.core.database import get_db
from app.features.workflows.service import WorkflowService, WorkflowRequest, WORKFLOW_DEFINITIONS


WORKFLOW_LABELS = {
    "daily_review": ("📋 每日回顾", "自动收集今日健康指标、评估风险并生成行动建议"),
    "medication_reconciliation": ("💊 药物核对", "核对今日用药计划并生成服药提醒"),
    "previsit_digest": ("🏥 门诊前准备", "生成包含近期趋势分析的临床 SOAP 摘要"),
    "adherence_followup": ("📊 依从性跟进", "识别服药和监测的依从性缺口"),
    "high_risk_escalation": ("🚨 高风险升级", "校验高风险条件并标记待跟进"),
}


def page_workflows():
    st.markdown('<div class="section-header">⚙️ 工作流引擎</div>', unsafe_allow_html=True)
    st.caption("确定性状态机驱动的临床工作流。每个工作流按步骤推进，支持日志回溯。")

    pid = st.session_state.active_patient_id
    tab_run, tab_history = st.tabs(["▶️ 执行工作流", "📜 执行历史"])

    # ── Tab 1: Run Workflow ──────────────────────────────
    with tab_run:
        st.subheader("选择工作流")

        for wf_type, (label, desc) in WORKFLOW_LABELS.items():
            definition = WORKFLOW_DEFINITIONS.get(wf_type)
            with st.container():
                cols = st.columns([4, 2])
                with cols[0]:
                    st.markdown(f"### {label}")
                    st.caption(desc)
                    if definition:
                        steps_str = " → ".join(definition.steps)
                        st.code(steps_str, language=None)
                with cols[1]:
                    st.markdown("")  # Spacer
                    if st.button(f"▶️ 执行", key=f"run_{wf_type}", use_container_width=True, type="primary"):
                        db = get_db()
                        try:
                            with st.spinner(f"正在执行 {label}..."):
                                service = WorkflowService(db, pid)
                                result = service.run(WorkflowRequest(workflow_type=wf_type))

                            if result.status == "completed":
                                st.success(f"✅ {label} 执行完成！")
                            elif result.status == "failed":
                                st.error(f"❌ {label} 执行失败")
                            else:
                                st.warning(f"⏳ {label} 状态: {result.status}")

                            if result.summary:
                                st.info(result.summary)

                            # Show step log
                            log = json.loads(result.log_json or "[]")
                            if log:
                                with st.expander("📋 执行日志"):
                                    for entry in log:
                                        status_icon = "✅" if entry.get("status") == "success" else "❌"
                                        st.markdown(f"{status_icon} **{entry.get('state')}** — {entry.get('at', '')}")
                        except Exception as e:
                            st.error(f"执行失败: {e}")
                        finally:
                            db.close()
                st.divider()

    # ── Tab 2: History ───────────────────────────────────
    with tab_history:
        st.subheader("工作流执行历史")
        db = get_db()
        try:
            runs = WorkflowService(db, pid).list_runs()
            if runs:
                for run in runs:
                    status_badge = {
                        "completed": "status-success",
                        "running": "status-info",
                        "failed": "status-danger",
                    }.get(run.status, "status-warning")

                    with st.expander(
                        f"{WORKFLOW_LABELS.get(run.workflow_type, ('', ''))[0] or run.workflow_type} "
                        f"— {run.created_at.strftime('%Y-%m-%d %H:%M')}",
                        expanded=False,
                    ):
                        st.markdown(
                            f'状态: <span class="status-badge {status_badge}">{run.status}</span> '
                            f'| 当前步骤: {run.current_state}',
                            unsafe_allow_html=True,
                        )
                        if run.summary:
                            st.info(run.summary)
                        log = json.loads(run.log_json or "[]")
                        if log:
                            for entry in log:
                                st.caption(f"  → {entry.get('state')} ({entry.get('status', '—')}) @ {entry.get('at', '—')}")
            else:
                st.info("暂无工作流执行记录。")
        finally:
            db.close()
