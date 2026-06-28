"""
Theme module — "Sky Palette" light design system.

Task 2: Theme Redesign — replaces the dark theme with a light,
weather-aware design that improves readability on projectors
and outdoor screens.

Usage:
    from theme import apply_theme, get_hero_gradient, get_alert_level
    apply_theme()  # call once at the top of each page
"""

import streamlit as st


# ── Design System Tokens ────────────────────────────────────────────────

THEME = {
    # Base surfaces
    "bg_page":      "#F0F7FF",   # light sky blue — morning sky feel
    "bg_card":      "#FFFFFF",
    "bg_sidebar":   "#EBF4FF",
    "bg_header":    "linear-gradient(135deg, #1D4ED8 0%, #2563EB 50%, #3B82F6 100%)",

    # Text
    "text_primary":   "#0F172A",  # near-black — high contrast on white
    "text_secondary": "#475569",
    "text_muted":     "#94A3B8",
    "text_on_hero":   "#FFFFFF",

    # Rain level badge colors (logic unchanged — only display colors)
    "no_rain":       {"bg": "#F0FDF4", "text": "#166534", "border": "#86EFAC"},
    "light_rain":    {"bg": "#ECFDF5", "text": "#065F46", "border": "#6EE7B7"},
    "moderate_rain": {"bg": "#FFF7ED", "text": "#9A3412", "border": "#FED7AA"},
    "heavy_rain":    {"bg": "#FFF1F2", "text": "#881337", "border": "#FECDD3"},
    "very_heavy":    {"bg": "#EDE9FE", "text": "#4C1D95", "border": "#C4B5FD"},

    # Map dot colors (aligned with README color guide)
    "map_green":  [34, 197, 94],     # < 40%
    "map_yellow": [250, 204, 21],    # 40–59%
    "map_orange": [249, 115, 22],    # 60–79%
    "map_red":    [239, 68, 68],     # ≥ 80%
}


# ── Global CSS Injection ────────────────────────────────────────────────

def apply_theme() -> None:
    """Inject global CSS for the Sky Palette light theme.

    Call once at the top of each page, right after st.set_page_config()
    or at the start of a page script.
    """
    st.markdown("""
    <style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* ── Page background ── */
    .stApp { background: #F0F7FF !important; }
    [data-testid="stAppViewContainer"] {
        background: #F0F7FF !important;
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #EBF4FF !important;
        border-right: 1px solid #BFDBFE !important;
    }
    [data-testid="stSidebar"] * { color: #0F172A !important; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        font-size: 13px;
        color: #475569 !important;
    }
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
        background: #DBEAFE !important;
        color: #1E40AF !important;
        border-radius: 9999px !important;
        font-size: 11px !important;
        border: 1px solid #93C5FD !important;
    }

    /* ── KPI metric cards ── */
    [data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1px solid #BFDBFE !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        box-shadow: 0 1px 6px rgba(37,99,235,0.08) !important;
    }
    [data-testid="stMetricLabel"] {
        color: #64748B !important;
        font-size: 12px !important;
        font-weight: 500 !important;
    }
    [data-testid="stMetricValue"] {
        color: #0F172A !important;
        font-size: 1.8rem !important;
        font-weight: 600 !important;
    }

    /* ── Data table ── */
    [data-testid="stDataFrame"] { background: #FFFFFF !important; }
    [data-testid="stDataFrame"] table { color: #0F172A !important; }
    [data-testid="stDataFrame"] thead th {
        background: #EFF6FF !important;
        color: #1E40AF !important;
        font-weight: 600 !important;
        font-size: 11px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    [data-testid="stDataFrame"] tbody tr:nth-child(odd) { background: #F8FAFF !important; }
    [data-testid="stDataFrame"] tbody tr:hover { background: #DBEAFE !important; }

    /* ── Expander (3-day accordion) ── */
    [data-testid="stExpander"] {
        background: #FFFFFF !important;
        border: 1px solid #BFDBFE !important;
        border-radius: 10px !important;
        margin-bottom: 6px !important;
    }
    [data-testid="stExpander"] summary { color: #1E40AF !important; font-weight: 500 !important; }

    /* ── Buttons ── */
    .stButton > button {
        background: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
    }
    .stButton > button:hover { background: #1D4ED8 !important; }
    .stButton > button[data-testid="baseButton-tertiary"] {
        background: #FFFFFF !important;
        color: #2563EB !important;
        border: 1px solid #93C5FD !important;
    }
    .stButton > button[data-testid="baseButton-tertiary"]:hover {
        background: #EFF6FF !important;
    }

    /* ── Download buttons ── */
    .stDownloadButton > button {
        background: #FFFFFF !important;
        color: #2563EB !important;
        border: 1px solid #93C5FD !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        width: 100% !important;
    }
    .stDownloadButton > button:hover {
        background: #EFF6FF !important;
        border-color: #2563EB !important;
    }

    /* ── Section headers ── */
    h1, h2, h3 { color: #0F172A !important; }
    h1 { font-size: 1.4rem !important; }
    h2 { font-size: 1.1rem !important; border-bottom: 1px solid #BFDBFE; padding-bottom: 6px; }

    /* ── Alert / info boxes ── */
    [data-testid="stAlert"] {
        background: #FFF7ED !important;
        border-left: 4px solid #F97316 !important;
        color: #7C2D12 !important;
        border-radius: 0 8px 8px 0 !important;
    }

    /* ── Selectbox / DateInput ── */
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stDateInput"] > div > div {
        background: #FFFFFF !important;
        border: 1px solid #93C5FD !important;
        border-radius: 8px !important;
        color: #0F172A !important;
    }

    /* ── Map container ── */
    iframe { border-radius: 12px !important; }

    /* ── Global font ── */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
    }

    /* ── Hero banner (light version) ── */
    .hero-banner {
        background: #FFFFFF;
        border: 1px solid #BFDBFE;
        border-radius: 12px;
        padding: 24px 32px;
        color: #0F172A;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .hero-banner .eyebrow {
        font-size: 12px;
        letter-spacing: -0.15px;
        color: #64748B;
        margin: 0 0 8px 0;
    }
    .hero-banner h1 {
        font-size: 48px;
        font-weight: 600;
        margin: 0 0 8px 0;
        color: #0F172A;
        letter-spacing: -1.056px;
        line-height: 1.0;
    }
    .hero-banner .hero-sub {
        font-size: 15px;
        color: #475569;
        margin: 0;
        letter-spacing: -0.165px;
    }
    .hero-banner .date-badge {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 8px;
        padding: 12px 20px;
        text-align: center;
    }
    .hero-banner .date-badge p {
        font-size: 11px;
        font-weight: 500;
        color: #64748B;
        margin: 0 0 4px 0;
    }
    .hero-banner .date-badge strong {
        font-size: 18px;
        font-weight: 600;
        color: #0F172A;
        letter-spacing: -0.165px;
    }

    /* ── Alert bar (light) ── */
    .alert-bar {
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 14px;
        margin-bottom: 24px;
    }
    .alert-bar.alert-warning {
        background: #FFF7ED;
        border: 1px solid #FED7AA;
        color: #7C2D12;
    }
    .alert-bar.alert-critical {
        background: #FEE2E2;
        border: 1px solid #FECACA;
        color: #7F1D1D;
    }

    /* ── Rain level badges (Sky Palette) ── */
    .badge-no-rain {
        background: #F0FDF4; color: #166534;
        border-radius: 9999px; padding: 2px 10px;
        border: 1px solid #86EFAC; font-size: 12px;
        font-weight: 500; display: inline-block;
    }
    .badge-light {
        background: #ECFDF5; color: #065F46;
        border-radius: 9999px; padding: 2px 10px;
        border: 1px solid #6EE7B7; font-size: 12px;
        font-weight: 500; display: inline-block;
    }
    .badge-moderate {
        background: #FFF7ED; color: #9A3412;
        border-radius: 9999px; padding: 2px 10px;
        border: 1px solid #FED7AA; font-size: 12px;
        font-weight: 500; display: inline-block;
    }
    .badge-heavy {
        background: #FFF1F2; color: #881337;
        border-radius: 9999px; padding: 2px 10px;
        border: 1px solid #FECDD3; font-size: 12px;
        font-weight: 500; display: inline-block;
    }
    .badge-veryheavy {
        background: #EDE9FE; color: #4C1D95;
        border-radius: 9999px; padding: 2px 10px;
        border: 1px solid #C4B5FD; font-size: 12px;
        font-weight: 500; display: inline-block;
    }

    /* ── Section card wrapper (light) ── */
    .section-card {
        background: #FFFFFF;
        border: 1px solid #BFDBFE;
        border-radius: 12px;
        padding: 0;
        margin-bottom: 24px;
        overflow: hidden;
    }
    .section-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 20px;
        border-bottom: 1px solid #E2E8F0;
        background: #FFFFFF;
        border-radius: 8px;
    }
    .section-card-header h3 {
        font-size: 15px;
        font-weight: 600;
        color: #0F172A;
        margin: 0;
        letter-spacing: -0.165px;
    }
    .section-card-header .legend {
        display: flex;
        gap: 12px;
        align-items: center;
        font-size: 13px;
        color: #64748B;
    }
    .section-card-header .legend .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }
    .section-card-body { padding: 16px 20px; }

    /* ── Forecast day cards (light) ── */
    .forecast-day-card {
        background: #F8FAFF;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        padding: 12px 14px;
    }
    .forecast-day-card .day-label {
        font-size: 11px;
        font-weight: 500;
        color: #64748B;
        margin: 0 0 6px 0;
    }
    .forecast-day-card .day-value {
        font-size: 13px;
        font-weight: 500;
        color: #0F172A;
        margin: 0;
    }

    /* ── Metric sub-labels ── */
    .metric-sub {
        font-size: 13px;
        color: #64748B;
        margin-top: 4px;
    }
    .metric-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
        vertical-align: middle;
    }

    /* ── Region header (flat display) ── */
    .region-header-flat {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 16px 0 8px 0;
        padding: 10px 16px;
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 8px;
    }
    .region-header-flat .region-dot-flat {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .region-header-flat .region-name {
        font-size: 14px;
        font-weight: 500;
        color: #0F172A;
    }
    .region-header-flat .region-count {
        font-size: 12px;
        color: #64748B;
    }

    /* ── Divider ── */
    hr { border-color: #BFDBFE !important; }
    </style>
    """, unsafe_allow_html=True)


# ── Weather-Aware Dynamic Theming ───────────────────────────────────────

def get_hero_gradient(rain_prob_avg: float) -> str:
    """Return CSS gradient string based on current weather severity.

    Args:
        rain_prob_avg: Average rain probability across filtered data.

    Returns:
        CSS linear-gradient string.
    """
    if rain_prob_avg < 40:
        # Clear / light — sky blue to cyan
        return "linear-gradient(135deg, #0EA5E9 0%, #38BDF8 50%, #7DD3FC 100%)"
    elif rain_prob_avg < 70:
        # Moderate — blue-grey to slate
        return "linear-gradient(135deg, #1E40AF 0%, #2563EB 50%, #6366F1 100%)"
    else:
        # Heavy / very heavy — deep blue to purple (stormy)
        return "linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4C1D95 100%)"


def get_alert_level(very_heavy_count: int) -> dict:
    """Return alert config for dynamic alert bar.

    Alert bar displays when very_heavy_count >= 10 (per README spec).

    Args:
        very_heavy_count: Number of locations with Very Heavy Rain.

    Returns:
        Dict with keys: show, level, color, bg, icon, msg, css_class.
    """
    if very_heavy_count >= 20:
        return {
            "show": True,
            "level": "critical",
            "icon": "🔴",
            "css_class": "alert-critical",
            "msg": f"Critical: {very_heavy_count} provinces with Very Heavy Rain",
        }
    elif very_heavy_count >= 10:
        return {
            "show": True,
            "level": "warning",
            "icon": "⚠️",
            "css_class": "alert-warning",
            "msg": f"Warning: {very_heavy_count} provinces with Very Heavy Rain",
        }
    else:
        return {"show": False}
