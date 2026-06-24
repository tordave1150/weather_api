import streamlit as st

def inject_custom_css():
    st.markdown("""
    <style>
    :root, [data-theme], [data-testid="stAppViewContainer"],
    [data-testid="stSidebar"], .main, .block-container {
        color-scheme: dark !important;
        background-color: #0e1117 !important;
        color: #fafafa !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #161b22 !important;
    }
    [data-testid="metric-container"] {
        background-color: #1a1d27 !important;
        border: 1px solid #2d3142 !important;
        border-radius: 8px;
        padding: 12px !important;
    }
    [data-testid="stDataFrame"] thead th {
        background-color: #1e2130 !important;
        color: #fafafa !important;
    }
    details summary, .streamlit-expanderHeader {
        background-color: #1e2130 !important;
        color: #fafafa !important;
    }
    .stSelectbox > div, .stDateInput > div, .stTextInput > div {
        background-color: #1e2130 !important;
        color: #fafafa !important;
    }
    .stButton > button:not([data-testid="baseButton-tertiary"]) {
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 6px !important;
        background: rgba(255, 255, 255, 0.02) !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #e2e4e7 !important;
    }
    .stButton > button:not([data-testid="baseButton-tertiary"]):hover {
        background: rgba(255, 255, 255, 0.05) !important;
        border-color: rgba(255, 255, 255, 0.15) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    /* ── CSS Variables (Linear Design System) ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    :root {
        --color-bg-tertiary: #08090a;
        --color-bg-primary: #0f1011;
        --color-bg-secondary: #191a1b;
        --color-border-tertiary: rgba(255, 255, 255, 0.08);
        --color-border-subtle: rgba(255, 255, 255, 0.05);
        --color-text-primary: #f7f8f8;
        --color-text-secondary: #d0d6e0;
        --color-text-tertiary: #8a8f98;
        --color-accent-blue: #5e6ad2;
        --color-info-blue: #7170ff;
        --color-teal: #10b981;
        --color-amber: #E89558;
        --color-red: #EA2143;
    }

    /* ── Reset & base ── */
    [data-testid="stAppViewContainer"] {
        background: var(--color-bg-tertiary) !important;
        font-family: 'Inter', sans-serif !important;
        font-feature-settings: "cv01", "ss03" !important;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: var(--color-bg-primary) !important;
        border-right: 1px solid var(--color-border-subtle) !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        font-size: 13px;
        color: var(--color-text-secondary);
    }
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
        background: rgba(255, 255, 255, 0.04) !important;
        color: var(--color-text-secondary) !important;
        border-radius: 9999px !important;
        font-size: 11px !important;
        border: 1px solid rgb(35, 37, 42) !important;
    }

    /* ── Metric cards ── */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid var(--color-border-tertiary) !important;
        border-radius: 8px !important;
        padding: 14px 16px !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 12px !important;
        font-weight: 500 !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        color: var(--color-text-tertiary) !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 32px !important;
        font-weight: 500 !important;
        letter-spacing: -0.704px !important;
        color: var(--color-text-primary) !important;
    }

    /* ── Dataframe table ── */
    [data-testid="stDataFrame"] th {
        font-size: 12px !important;
        font-weight: 500 !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        color: var(--color-text-tertiary) !important;
    }

    /* ── Buttons ── */
    .stDownloadButton > button {
        border: 1px solid var(--color-border-tertiary) !important;
        border-radius: 6px !important;
        background: rgba(255, 255, 255, 0.02) !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #e2e4e7 !important;
        width: 100% !important;
    }
    .stDownloadButton > button:hover {
        background: rgba(255, 255, 255, 0.05) !important;
    }

    /* ── Hero banner ── */
    .hero-banner {
        background: var(--color-bg-primary);
        border: 1px solid var(--color-border-tertiary);
        border-radius: 12px;
        padding: 24px 32px;
        color: var(--color-text-primary);
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .hero-banner .hero-left {}
    .hero-banner .eyebrow {
        font-size: 12px;
        letter-spacing: -0.15px;
        text-transform: none;
        color: var(--color-text-tertiary);
        margin: 0 0 8px 0;
    }
    .hero-banner h1 {
        font-size: 48px;
        font-weight: 500;
        margin: 0 0 8px 0;
        color: var(--color-text-primary);
        letter-spacing: -1.056px;
        line-height: 1.0;
    }
    .hero-banner .hero-sub {
        font-size: 15px;
        color: var(--color-text-secondary);
        margin: 0;
        letter-spacing: -0.165px;
    }
    .hero-banner .date-badge {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid var(--color-border-subtle);
        border-radius: 8px;
        padding: 12px 20px;
        text-align: center;
    }
    .hero-banner .date-badge p {
        font-size: 11px;
        font-weight: 500;
        text-transform: none;
        color: var(--color-text-tertiary);
        margin: 0 0 4px 0;
    }
    .hero-banner .date-badge strong {
        font-size: 18px;
        font-weight: 500;
        color: var(--color-text-primary);
        letter-spacing: -0.165px;
    }

    /* ── Alert bar ── */
    .alert-bar {
        background: rgba(234, 33, 67, 0.1);
        border: 1px solid rgba(234, 33, 67, 0.2);
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 14px;
        color: var(--color-red);
        margin-bottom: 24px;
    }

    /* ── Section card wrapper ── */
    .section-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 20px;
        border-bottom: 1px solid var(--color-border-subtle);
        background: rgba(255, 255, 255, 0.02);
        border-radius: 8px;
    }
    .section-card-header h3 {
        font-size: 15px;
        font-weight: 500;
        color: var(--color-text-primary);
        margin: 0;
        letter-spacing: -0.165px;
    }
    </style>
    """, unsafe_allow_html=True)
