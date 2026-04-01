"""Theme helper with consistent readable light-medical tokens."""
import streamlit as st


def inject_custom_css():
    st.markdown(
        """
<style>
:root {
  --cp-bg: #f4f7fb;
  --cp-surface: #ffffff;
  --cp-text: #10243e;
  --cp-text-muted: #4a607b;
  --cp-border: #d9e2ef;
  --cp-primary: #2364d2;
  --cp-success: #1f8f5f;
  --cp-warning: #b26a00;
}

.stApp { background: var(--cp-bg); color: var(--cp-text); }
footer, #MainMenu, .stDeployButton { visibility: hidden; }

section[data-testid="stSidebar"] {
  background: var(--cp-surface);
  border-right: 1px solid var(--cp-border);
}

h1, h2, h3, h4, p, span, label, .stMarkdown, .stCaption {
  color: var(--cp-text);
}

.stCaption, small { color: var(--cp-text-muted) !important; }

div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"] {
  background: var(--cp-surface);
  border: 1px solid var(--cp-border) !important;
  border-radius: 12px;
}

.stButton > button {
  border-radius: 10px;
  border: 1px solid var(--cp-border);
}

.stButton > button[kind="primary"] {
  background: var(--cp-primary);
  color: #fff;
  border-color: var(--cp-primary);
}
</style>
""",
        unsafe_allow_html=True,
    )
