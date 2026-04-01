"""
Reports page — Generate and export health reports (Markdown, DOCX, PDF, HTML).
"""
import streamlit as st

from app.core.database import get_db
from app.features.reports.service import ReportService, ReportRequest


def page_reports():
    st.markdown('<div class="section-header">📋 健康报告</div>', unsafe_allow_html=True)

    pid = st.session_state.active_patient_id
    tab_generate, tab_history = st.tabs(["📝 生成报告", "📚 历史报告"])

    # ── Tab 1: Generate Report ───────────────────────────
    with tab_generate:
        st.subheader("生成新报告")
        with st.form("report_form"):
            report_type = st.selectbox(
                "报告类型",
                [
                    ("patient_weekly", "📊 患者周报"),
                    ("clinician_previsit", "🏥 门诊前摘要"),
                    ("adherence_overview", "💊 依从性概览"),
                ],
                format_func=lambda x: x[1],
                index=0,
            )
            window_days = st.slider("回溯天数", 3, 30, 7)
            submitted = st.form_submit_button("📄 生成报告", use_container_width=True, type="primary")

        if submitted:
            db = get_db()
            try:
                service = ReportService(db, pid)
                with st.spinner("正在生成报告..."):
                    result = service.generate(ReportRequest(
                        report_type=report_type[0],
                        window_days=window_days,
                    ))

                st.success(f"✅ 报告「{result['title']}」已生成！")

                # Display report
                st.markdown("---")
                st.markdown(result["markdown"])

                # Export buttons
                st.markdown("---")
                st.subheader("📥 导出")
                exp1, exp2, exp3 = st.columns(3)
                report_id = result["id"]

                with exp1:
                    try:
                        docx_bytes = service.export_docx(report_id)
                        st.download_button(
                            "📄 下载 DOCX",
                            data=docx_bytes,
                            file_name=f"report_{report_id}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                        )
                    except ImportError:
                        st.caption("需安装 python-docx")

                with exp2:
                    html_content = service.export_html(report_id)
                    st.download_button(
                        "🌐 下载 HTML",
                        data=html_content,
                        file_name=f"report_{report_id}.html",
                        mime="text/html",
                        use_container_width=True,
                    )

                with exp3:
                    try:
                        pdf_bytes = service.export_pdf(report_id)
                        st.download_button(
                            "📑 下载 PDF",
                            data=pdf_bytes,
                            file_name=f"report_{report_id}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except ImportError:
                        st.caption("需安装 reportlab")

            except Exception as e:
                st.error(f"生成失败: {e}")
            finally:
                db.close()

    # ── Tab 2: History ───────────────────────────────────
    with tab_history:
        st.subheader("历史报告")
        db = get_db()
        try:
            reports = ReportService(db, pid).list_reports()
            if reports:
                for r in reports:
                    with st.expander(f"📄 {r['title']} — {r['created_at'].strftime('%Y-%m-%d %H:%M')}", expanded=False):
                        st.markdown(r["markdown"])
                        st.caption(f"类型: {r['report_type']} | ID: {r['id']}")
            else:
                st.info("暂无历史报告。请在「生成报告」中创建。")
        finally:
            db.close()
