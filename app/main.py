"""
Weather Advisor — Streamlit Dashboard (main entry point).

Read-only dashboard that displays weather forecast data for all 77 Thai provinces.
Data is fetched by the ETL script (etl/fetch_weather.py) and stored in MongoDB Atlas.

Run with: streamlit run app/main.py
"""

import json
import pathlib

import streamlit as st
import pandas as pd

from db import get_db, get_forecasts
from components.sidebar import render_sidebar
from components.map_view import render_map
from components.export import render_export

# ── Page Config ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Weather Advisor",
    page_icon="⛈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design System CSS (Spec Section 4) ────────────────────────────────
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

/* ── Rain level badges (Linear pill style) ── */
.badge-no-rain    { background: transparent; color: var(--color-text-secondary); border-radius: 9999px; padding: 2px 10px 2px 10px; border: 1px solid rgb(35,37,42); font-size: 12px; font-weight: 500; display: inline-block; }
.badge-light      { background: transparent; color: var(--color-info-blue); border-radius: 9999px; padding: 2px 10px 2px 10px; border: 1px solid rgba(113, 112, 255, 0.3); font-size: 12px; font-weight: 500; display: inline-block; }
.badge-moderate   { background: transparent; color: var(--color-teal); border-radius: 9999px; padding: 2px 10px 2px 10px; border: 1px solid rgba(16, 185, 129, 0.3); font-size: 12px; font-weight: 500; display: inline-block; }
.badge-heavy      { background: transparent; color: var(--color-amber); border-radius: 9999px; padding: 2px 10px 2px 10px; border: 1px solid rgba(232, 149, 88, 0.3); font-size: 12px; font-weight: 500; display: inline-block; }
.badge-veryheavy  { background: transparent; color: var(--color-red); border-radius: 9999px; padding: 2px 10px 2px 10px; border: 1px solid rgba(234, 33, 67, 0.3); font-size: 12px; font-weight: 500; display: inline-block; }

/* ── Section card wrapper ── */
.section-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--color-border-tertiary);
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
    border-bottom: 1px solid var(--color-border-subtle);
}
.section-card-header h3 {
    font-size: 15px;
    font-weight: 500;
    color: var(--color-text-primary);
    margin: 0;
    letter-spacing: -0.165px;
}
.section-card-header .legend {
    display: flex;
    gap: 12px;
    align-items: center;
    font-size: 13px;
    color: var(--color-text-tertiary);
}
.section-card-header .legend .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 6px;
}
.section-card-body {
    padding: 16px 20px;
}

/* ── Forecast day cards ── */
.forecast-day-card {
    background: rgba(255, 255, 255, 0.02);
    border-radius: 6px;
    border: 1px solid var(--color-border-subtle);
    padding: 12px 14px;
}
.forecast-day-card .day-label {
    font-size: 11px;
    font-weight: 500;
    color: var(--color-text-tertiary);
    margin: 0 0 6px 0;
}
.forecast-day-card .day-value {
    font-size: 13px;
    font-weight: 500;
    color: var(--color-text-primary);
    margin: 0;
}

/* ── Region dots ── */
.region-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 8px;
    vertical-align: middle;
}

/* ── Metric sub-labels ── */
.metric-sub {
    font-size: 13px;
    color: var(--color-text-tertiary);
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

/* ── FEAT-03: Region header (flat display) ── */
.region-header-flat {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 16px 0 8px 0;
    padding: 10px 16px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--color-border-tertiary);
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
    color: var(--color-text-primary);
}
.region-header-flat .region-count {
    font-size: 12px;
    color: var(--color-text-tertiary);
}
</style>
""", unsafe_allow_html=True)

# ── Helper Functions ──────────────────────────────────────────────────

def get_rain_emoji(level: str) -> str:
    """Return weather emoji for rain level string."""
    mapping = {
        "No Rain": "☀️",
        "Light Rain": "🌤",
        "Moderate Rain": "🌦",
        "Heavy Rain": "🌧",
        "Very Heavy Rain": "⛈",
    }
    return mapping.get(level, "🌡")


def get_rain_badge_html(level: str) -> str:
    """Return HTML badge for rain level."""
    cls_map = {
        "No Rain": "badge-no-rain",
        "Light Rain": "badge-light",
        "Moderate Rain": "badge-moderate",
        "Heavy Rain": "badge-heavy",
        "Very Heavy Rain": "badge-veryheavy",
    }
    cls = cls_map.get(level, "badge-no-rain")
    return f'<span class="{cls}">{level}</span>'


REGION_DOT_COLORS = {
    "Central": "#378ADD",
    "Northern": "#E24B4A",
    "Northeastern": "#EF9F27",
    "Eastern": "#1D9E75",
    "Southern": "#7F77DD",
    "Western": "#888780",
}


# ── Load province/district coords for enrichment ─────────────────────
@st.cache_data
def load_provinces():
    """Load the static provinces.json for lat/lon coordinates."""
    path = pathlib.Path(__file__).resolve().parent.parent / "data" / "provinces.json"
    with open(path, "r", encoding="utf-8") as f:
        provinces = json.load(f)
    return {p["province"]: p for p in provinces}


@st.cache_data
def load_districts():
    """Load the static districts.json for lat/lon coordinates."""
    path = pathlib.Path(__file__).resolve().parent.parent / "data" / "districts.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        districts = json.load(f)
    return {d["district"]: d for d in districts}


province_coords = load_provinces()
district_coords = load_districts()

# ── MongoDB Connection ────────────────────────────────────────────────
try:
    collection = get_db()
except Exception as e:
    st.error(
        "🔒 **MongoDB connection failed.** Please check your credentials in "
        "`.streamlit/secrets.toml`.\n\n"
        f"Error: `{type(e).__name__}`"
    )
    st.stop()

# ── Sidebar Filters ───────────────────────────────────────────────────
try:
    available_provinces = sorted(list(province_coords.keys()))
    available_districts = sorted(list(district_coords.keys()))
    filters = render_sidebar(collection, available_provinces, available_districts)
except Exception as e:
    st.error(
        "🔒 **MongoDB authentication failed.** The database rejected the credentials.\n\n"
        "Please verify the `uri`, `db_name`, and `collection` values in "
        "`.streamlit/secrets.toml`.\n\n"
        f"Error: `{type(e).__name__}`"
    )
    st.stop()

selected_date = filters["selected_date"]
selected_regions = filters["regions"]
selected_rain_levels = filters["rain_levels"]
province_search = filters.get("province_search", "")
level = filters.get("level", "province")
selected_province = filters.get("selected_province")

# ── Fetch Data ────────────────────────────────────────────────────────
raw_data = get_forecasts(
    collection, selected_date,
    selected_regions if selected_regions else None,
    level=level,
)

# Apply filters client-side
data = raw_data
if selected_rain_levels:
    data = [d for d in data if d.get("rain_level") in selected_rain_levels]

# Province scope filter (district mode)
if level == "district" and selected_province:
    data = [d for d in data if d.get("province") == selected_province]

# Text search filter
if province_search:
    search_lower = province_search.lower()
    if level == "district":
        data = [d for d in data if search_lower in d.get("district", "").lower()]
    else:
        data = [d for d in data if search_lower in d.get("province", "").lower()]

# Enrich with lat/lon from static data (in case MongoDB docs don't have them)
for doc in data:
    if level == "district":
        dist_name = doc.get("district", "")
        if dist_name in district_coords:
            doc["lat"] = district_coords[dist_name]["lat"]
            doc["lon"] = district_coords[dist_name]["lon"]
    else:
        prov_name = doc.get("province", "")
        if prov_name in province_coords:
            doc["lat"] = province_coords[prov_name]["lat"]
            doc["lon"] = province_coords[prov_name]["lon"]

# ── KPI calculations ─────────────────────────────────────────────────
total_locations = len(data)
high_rain = sum(1 for d in data if d.get("rain_probability", 0) >= 40)
very_heavy = sum(1 for d in data if d.get("rain_level") == "Very Heavy Rain")
avg_prob = round(sum(d.get("rain_probability", 0) for d in data) / max(total_locations, 1), 1)

# Level-aware labels
location_label = "Districts" if level == "district" else "Provinces"
location_label_lower = "districts" if level == "district" else "provinces"

# ── Refresh time extraction ──────────────────────────────────────────
_refresh_time = "—"
_fetch_round = ""
if data:
    # Find the most recent logged_at across all documents
    logged_times = [d.get("logged_at", "") for d in data if d.get("logged_at")]
    if logged_times:
        latest_log = max(logged_times)
        try:
            from datetime import datetime as _dt
            _parsed = _dt.fromisoformat(latest_log)
            _refresh_time = _parsed.strftime("%H:%M")
        except Exception:
            _refresh_time = latest_log[:16]
    _fetch_round = data[0].get("fetch_round", "")

_round_label = f' · {_fetch_round.capitalize()} round' if _fetch_round else ""

# ── Hero Banner ───────────────────────────────────────────────────────
eyebrow_text = "Thailand District Weather Forecast" if level == "district" else "Thailand Provincial Weather Forecast"
st.markdown(f"""
<div class="hero-banner">
    <div class="hero-left">
        <p class="eyebrow">{eyebrow_text}</p>
        <h1>⛈ Weather Advisor</h1>
        <p class="hero-sub">{total_locations} {location_label_lower} displayed · Data updated daily from Open-Meteo</p>
    </div>
    <div class="date-badge">
        <p>Data Date</p>
        <strong>{selected_date}</strong>
        <p style="font-size:10px; color:var(--color-text-tertiary); margin:6px 0 0 0;">
            Refreshed {_refresh_time}{_round_label}
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Alert Bar ─────────────────────────────────────────────────────────
if very_heavy >= 10:
    st.markdown(f"""
    <div class="alert-bar">
        ⚠️ <strong>Heavy rain advisory:</strong> {very_heavy} {location_label_lower} are currently forecasting Very Heavy Rain — plan outdoor activities accordingly.
    </div>
    """, unsafe_allow_html=True)

# ── KPI Metric Cards ─────────────────────────────────────────────────
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric(f"Total {location_label}", total_locations)
    st.markdown('<p class="metric-sub">All regions included</p>', unsafe_allow_html=True)
with kpi2:
    st.metric("High Rain Zones", high_rain)
    st.markdown('<p class="metric-sub">≥ 40% rain probability</p>', unsafe_allow_html=True)
with kpi3:
    st.metric("Very Heavy Rain", very_heavy)
    st.markdown('<p class="metric-sub">Exceeds 35 mm/day</p>', unsafe_allow_html=True)
with kpi4:
    st.metric("Avg Rain Probability", f"{avg_prob}%")
    st.markdown(f'<p class="metric-sub">Across all {total_locations} {location_label_lower}</p>', unsafe_allow_html=True)

# ── Map Side-by-Side (Predicted vs Current) ───────────────────────────
col_map_pred, col_map_curr = st.columns(2)

with col_map_pred:
    map_title_pred = f"🗺️ Predicted Daily Rain ({location_label})"
    st.markdown(f"""
    <div class="section-card-header">
        <h3>{map_title_pred}</h3>
        <div class="legend">
            <span><span class="dot" style="background:#1D9E75;"></span>Mod</span>
            <span><span class="dot" style="background:#EF9F27;"></span>Heavy</span>
            <span><span class="dot" style="background:#E24B4A;"></span>V.Heavy</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    render_map(data, level=level, map_type="predicted")

with col_map_curr:
    map_title_curr = f"📡 Current Rain (Latest Refresh) ({location_label})"
    st.markdown(f"""
    <div class="section-card-header">
        <h3>{map_title_curr}</h3>
        <div class="legend">
            <span><span class="dot" style="background:#1D9E75;"></span>Mod</span>
            <span><span class="dot" style="background:#EF9F27;"></span>Heavy</span>
            <span><span class="dot" style="background:#E24B4A;"></span>V.Heavy</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    render_map(data, level=level, map_type="current")

# ── 3-Day Forecast — FLAT DISPLAY (FEAT-03) ──────────────────────────
# Date range for header
if data and data[0].get("forecast_3_days"):
    fc_dates = [fc.get("date", "") for fc in data[0]["forecast_3_days"]]
    date_range_str = f"{selected_date[5:]} – {fc_dates[-1][5:]}" if fc_dates else ""
else:
    date_range_str = ""

st.markdown(f"""
<div class="section-card-header" style="margin-top: 8px; background: var(--color-bg-primary); border-radius: 12px 12px 0 0; border: 0.5px solid var(--color-border-tertiary); border-bottom: none;">
    <h3>📅 3-Day Forecast by Region</h3>
    <div class="legend"><span>{date_range_str}</span></div>
</div>
""", unsafe_allow_html=True)

if data:
    # Group data by region
    grouped = {}
    for d in data:
        reg = d.get("region", "Unknown")
        grouped.setdefault(reg, []).append(d)

    region_order = ["Central", "Northern", "Northeastern", "Eastern", "Southern", "Western"]
    regions_in_data = [r for r in region_order if r in set(d.get("region", "") for d in data)]
    count_label = "districts" if level == "district" else "provinces"

    for region in regions_in_data:
        docs = grouped.get(region, [])
        if not docs:
            continue
            
        # Sort docs by highest rain prob today
        docs_sorted = sorted(docs, key=lambda x: x.get("rain_probability", 0), reverse=True)
        
        with st.expander(f"{region} Region ({len(docs)} {count_label})"):
            for d in docs_sorted:
                loc_name = d.get("district") or d.get("province", "Unknown")
                prob = d.get("rain_probability", 0)
                emoji = get_rain_emoji(d.get("rain_level", ""))
                
                st.markdown(f"""
                <div class="list-item">
                    <span class="loc-name">{loc_name}</span>
                    <span class="badge" style="background: rgba(255,255,255,0.05); color: #ccc;">
                        Today: {emoji} {prob}%
                    </span>
                </div>
                """, unsafe_allow_html=True)

                forecast = d.get("forecast_3_days", [])
                if forecast:
                    fcols = st.columns(len(forecast))
                    for i, fc in enumerate(forecast):
                        fc_level = fc.get("level", "")
                        fc_emoji = get_rain_emoji(fc_level)
                        fc_date = fc.get("date", "")
                        try:
                            from datetime import datetime
                            dt = datetime.strptime(fc_date, "%Y-%m-%d")
                            fc_date_short = dt.strftime("%b %d")
                        except Exception:
                            fc_date_short = fc_date
                            
                        # Dynamic color logic for cards
                        if fc_level == "Very Heavy Rain":
                            bg_color = "rgba(226, 75, 74, 0.15)"
                            text_color = "var(--color-red)"
                        elif fc_level == "Heavy Rain":
                            bg_color = "rgba(239, 159, 39, 0.15)"
                            text_color = "var(--color-amber)"
                        elif fc_level == "Moderate Rain":
                            bg_color = "rgba(16, 185, 129, 0.15)"
                            text_color = "var(--color-teal)"
                        elif fc_level == "Light Rain":
                            bg_color = "rgba(113, 112, 255, 0.15)"
                            text_color = "var(--color-info-blue)"
                        else:
                            bg_color = "rgba(255, 255, 255, 0.02)"
                            text_color = "var(--color-text-primary)"

                        with fcols[i]:
                            st.markdown(f"""
                            <div class="forecast-day-card" style="background: {bg_color}; border-color: {bg_color};">
                                <p class="day-label">Day+{i+1} · {fc_date_short}</p>
                                <p class="day-value" style="color: {text_color};">{fc_emoji} {fc_level} ({fc.get('rain_prob', 0)}%)</p>
                            </div>
                            """, unsafe_allow_html=True)
                st.divider()
else:
    st.info("No forecast data available. Run the ETL script first: `python etl/fetch_weather.py`")

# ── Export Buttons (sidebar) ──────────────────────────────────────────
render_export(data, selected_date, level=level)

# ── Footer ────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("⛈ Weather Advisor • Data source: Open-Meteo API • Storage: MongoDB Atlas")
