"""CarePilot CN — Central Brand & Design System with Light Medical Theme."""
import streamlit as st


def inject_custom_css():
    """Injects premium CSS for a cohesive medical product experience."""
    st.markdown(
        """
<style>
/* 1. Design Tokens — Light Medical Theme */
:root {
  --cp-bg: #f8fafc;
  --cp-surface: #ffffff;
  --cp-text: #0f172a;
  --cp-text-muted: #64748b;
  --cp-border: #e2e8f0;
  
  --cp-primary: #2563eb;
  --cp-primary-soft: #eff6ff;
  
  --cp-success: #16a34a;
  --cp-success-soft: #f0fdf4;
  
  --cp-warning: #ea580c;
  --cp-warning-soft: #fff7ed;
  
  --cp-error: #dc2626;
  --cp-error-soft: #fef2f2;
  
  --radius-lg: 16px;
  --radius-md: 12px;
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}

/* 2. Base Modernization */
.stApp {
  background-color: var(--cp-bg) !important;
  color: var(--cp-text) !important;
}

/* Fix global font issues */
h1, h2, h3, h4, p, span, label, .stMarkdown, .stCaption, .st-emotion-cache-1vt4y43 {
  color: var(--cp-text) !important;
}

/* 3. Streamlit Component Overrides */
/* Sidebar styling */
section[data-testid="stSidebar"] {
  background: var(--cp-surface) !important;
  border-right: 1px solid var(--cp-border) !important;
  box-shadow: var(--shadow-sm);
}

/* Card Container Overrides (st.container(border=True)) */
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--cp-surface);
  border: 1px solid var(--cp-border) !important;
  border-radius: var(--radius-md) !important;
  padding: 1rem;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
}

/* Button Modernization */
.stButton > button {
  border-radius: 20px !important;
  font-weight: 500 !important;
  border: 1px solid var(--cp-border) !important;
  transition: all 0.2s ease !important;
}

.stButton > button:hover {
  border-color: var(--cp-primary) !important;
  color: var(--cp-primary) !important;
  background: var(--cp-primary-soft) !important;
}

.stButton > button[kind="primary"] {
  background: var(--cp-primary) !important;
  color: white !important;
  border: none !important;
}

.stButton > button[kind="primary"]:hover {
  background: #1d4ed8 !important; /* Slightly darker than primary */
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}

/* Input Fields */
.stTextInput > div > div > input, 
.stSelectbox > div > div > div,
.stTextArea > div > div > textarea {
  border-radius: var(--radius-md) !important;
  background: var(--cp-surface) !important;
  border-color: var(--cp-border) !important;
}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
  gap: 8px;
  background-color: transparent !important;
}

.stTabs [data-baseweb="tab"] {
  border-radius: 8px 8px 0 0 !important;
  background-color: transparent !important;
  padding: 8px 16px !important;
}

/* Custom Header Styling */
.section-header {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: var(--cp-text);
  border-left: 4px solid var(--cp-primary);
  padding-left: 1rem;
}

/* Chat Input Styling */
.stChatInput {
  border-radius: 30px !important;
  box-shadow: 0 -4px 10px rgba(0,0,0,0.02) !important;
}

/* Hide Branding */
footer {visibility: hidden;}
header {visibility: hidden;}

</style>
""",
        unsafe_allow_html=True,
    )
