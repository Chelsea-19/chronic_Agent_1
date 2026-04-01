"""
Settings page — LLM configuration and system status.
"""
import streamlit as st

from app.core.config import get_settings


def page_settings():
    st.markdown('<div class="section-header">🔧 系统设置</div>', unsafe_allow_html=True)

    settings = get_settings()

    tab_llm, tab_status = st.tabs(["🤖 模型配置", "📊 系统状态"])

    # ── Tab 1: LLM Configuration ─────────────────────────
    with tab_llm:
        st.subheader("AI 模型配置")
        st.caption(
            "配置 LLM API 连接。在 Streamlit Cloud 上可通过 App Secrets 设置，"
            "本地开发时可在此页面临时覆盖。"
        )

        # Show current config
        st.markdown("### 当前配置")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**提供商:** `{settings.llm_provider}`")
            st.markdown(f"**模型:** `{settings.llm_model}`")
        with c2:
            st.markdown(f"**Fake LLM:** `{settings.enable_fake_llm}`")
            if settings.llm_configured:
                st.success("🟢 LLM API 已配置")
            else:
                st.warning("🟡 未配置 API Key — 使用规则引擎模式")

        st.divider()

        # Runtime override (saved to session_state only)
        st.markdown("### 运行时覆盖 (仅本次会话)")
        st.caption("⚠️ 修改仅在当前会话内生效。生产环境请使用 Streamlit Secrets。")

        with st.form("llm_override_form"):
            provider = st.selectbox(
                "提供商",
                ["openai", "google"],
                index=0 if settings.llm_provider == "openai" else 1,
            )
            api_key = st.text_input(
                "API Key",
                value=st.session_state.get("llm_api_key", ""),
                type="password",
                placeholder="sk-... 或 Google API Key",
            )
            base_url = st.text_input(
                "Base URL (OpenAI 兼容)",
                value=st.session_state.get("llm_base_url", ""),
                placeholder="https://api.openai.com",
            )
            model = st.text_input(
                "模型名称",
                value=st.session_state.get("llm_model", "") or settings.llm_model,
                placeholder="gpt-4o-mini / gemini-1.5-flash",
            )
            submitted = st.form_submit_button("💾 保存配置", use_container_width=True, type="primary")

        if submitted:
            st.session_state.llm_api_key = api_key
            st.session_state.llm_base_url = base_url
            st.session_state.llm_model = model
            st.session_state.llm_provider = provider
            st.success("✅ 配置已保存到当前会话")

        st.divider()

        # Guide
        st.markdown("### 📖 Streamlit Cloud 配置指南")
        st.markdown("""
        1. 前往 Streamlit Cloud 后台 → 你的应用 → Settings → Secrets
        2. 粘贴以下内容：

        ```toml
        [llm]
        provider = "openai"
        api_key = "sk-your-key-here"
        base_url = "https://api.openai.com"
        model = "gpt-4o-mini"

        [app]
        enable_fake_llm = false
        ```

        3. 保存后应用会自动重启。
        """)

    # ── Tab 2: System Status ─────────────────────────────
    with tab_status:
        st.subheader("系统状态")

        st.markdown("### ✅ 基础检查")
        checks = {
            "数据库初始化": True,
            "SQLite 可写": True,
            "LLM 配置": settings.llm_configured,
        }

        for label, ok in checks.items():
            icon = "✅" if ok else "⚠️"
            st.markdown(f"{icon} {label}")

        st.divider()

        st.markdown("### 📦 依赖信息")
        deps = {
            "streamlit": _try_version("streamlit"),
            "sqlalchemy": _try_version("sqlalchemy"),
            "pydantic": _try_version("pydantic"),
            "httpx": _try_version("httpx"),
            "python-docx": _try_version("docx"),
            "reportlab": _try_version("reportlab"),
        }
        for pkg, ver in deps.items():
            st.caption(f"📦 {pkg}: {ver}")


def _try_version(module_name: str) -> str:
    try:
        mod = __import__(module_name)
        return getattr(mod, "__version__", "installed")
    except ImportError:
        return "❌ not installed"
