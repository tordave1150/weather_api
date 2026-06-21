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
from components.table_view import render_table
from components.export import render_export

# ── Page Config ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Weather Advisor",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for premium look ───────────────────────────────────────
st.markdown("""
<style>
    /* Main container */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1a237e 0%, #0d47a1 50%, #01579b 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .main-header p {
        color: rgba(255, 255, 255, 0.85);
        margin: 0.3rem 0 0 0;
        font-size: 0.95rem;
    }

    /* KPI card styling */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8eaf6 100%);
        border: 1px solid #c5cae9;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        font-weight: 600;
        color: #37474f;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1a237e;
    }

    /* Section headers */
    .section-header {
        font-size: 1.15rem;
        font-weight: 600;
        color: #263238;
        padding: 0.5rem 0;
        border-bottom: 2px solid #1a237e;
        margin: 1rem 0 0.8rem 0;
    }

    /* Sidebar branding */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fafafa 0%, #f0f0f0 100%);
    }
</style>
""", unsafe_allow_html=True)

# ── Load province lat/lon for map enrichment ──────────────────────────
@st.cache_data
def load_provinces():
    """Load the static provinces.json for lat/lon coordinates."""
    path = pathlib.Path(__file__).resolve().parent.parent / "data" / "provinces.json"
    with open(path, "r", encoding="utf-8") as f:
        provinces = json.load(f)
    return {p["province"]: p for p in provinces}


province_coords = load_provinces()

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
    filters = render_sidebar(collection, available_provinces)
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
selected_provinces = filters.get("provinces", [])

# ── Fetch Data ────────────────────────────────────────────────────────
raw_data = get_forecasts(collection, selected_date, selected_regions if selected_regions else None)

# Apply filters client-side
data = raw_data
if selected_rain_levels:
    data = [d for d in data if d.get("rain_level") in selected_rain_levels]
if selected_provinces:
    data = [d for d in data if d.get("province") in selected_provinces]

# Enrich with lat/lon from provinces.json (in case MongoDB docs don't have them)
for doc in data:
    prov_name = doc.get("province", "")
    if prov_name in province_coords:
        doc["lat"] = province_coords[prov_name]["lat"]
        doc["lon"] = province_coords[prov_name]["lon"]

# ── Header ────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
    <h1>🌦️ Weather Advisor</h1>
    <p>Thailand Provincial Weather Forecast Dashboard &nbsp;•&nbsp; Data Date: <strong>{selected_date}</strong> &nbsp;•&nbsp; {len(data)} provinces displayed</p>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────────────
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_provinces = len(data)
high_rain = sum(1 for d in data if d.get("rain_probability", 0) >= 60)
very_heavy = sum(1 for d in data if d.get("rain_level") == "Very Heavy Rain")
avg_prob = round(sum(d.get("rain_probability", 0) for d in data) / max(total_provinces, 1), 1)

with kpi1:
    st.metric("🏘️ Total Provinces", total_provinces)
with kpi2:
    st.metric("⚠️ High Rain Zones", high_rain)
with kpi3:
    st.metric("🌊 Very Heavy Rain", very_heavy)
with kpi4:
    st.metric("📊 Avg Rain Prob", f"{avg_prob}%")

# ── Map View ──────────────────────────────────────────────────────────
st.markdown('<p class="section-header">🗺️ Province Rain Map</p>', unsafe_allow_html=True)
render_map(data)

# ── Data Table ────────────────────────────────────────────────────────
st.markdown('<p class="section-header">📋 Province Forecast Data</p>', unsafe_allow_html=True)
render_table(data)

# ── 3-Day Forecast Expander ───────────────────────────────────────────
st.markdown('<p class="section-header">📅 3-Day Forecast Details</p>', unsafe_allow_html=True)

if data:
    # Group by region for organized display
    regions_in_data = sorted(set(d.get("region", "") for d in data))
    for region in regions_in_data:
        region_data = [d for d in data if d.get("region") == region]
        with st.expander(f"🌐 {region} ({len(region_data)} provinces)", expanded=False):
            for doc in region_data:
                forecast = doc.get("forecast_3_days", [])
                province_name = doc.get("province", "Unknown")
                rain_level = doc.get("rain_level", "")

                # Emoji indicator
                level_emoji = {
                    "No Rain": "☀️",
                    "Light Rain": "🌤️",
                    "Moderate Rain": "🌦️",
                    "Heavy Rain": "🌧️",
                    "Very Heavy Rain": "⛈️",
                }.get(rain_level, "🌡️")

                st.markdown(f"**{level_emoji} {province_name}** — Today: {rain_level} ({doc.get('rain_probability', 0)}%)")

                if forecast:
                    fcols = st.columns(len(forecast))
                    for i, fc in enumerate(forecast):
                        fc_emoji = {
                            "No Rain": "☀️",
                            "Light Rain": "🌤️",
                            "Moderate Rain": "🌦️",
                            "Heavy Rain": "🌧️",
                            "Very Heavy Rain": "⛈️",
                        }.get(fc.get("level", ""), "🌡️")
                        with fcols[i]:
                            st.caption(f"Day+{i+1}: {fc.get('date', '')}")
                            st.write(f"{fc_emoji} {fc.get('level', '')} ({fc.get('rain_prob', 0)}%)")
                st.divider()
else:
    st.info("No forecast data available. Run the ETL script first: `python etl/fetch_weather.py`")


# ── Export Buttons (sidebar) ──────────────────────────────────────────
render_export(data, selected_date)

# ── Footer ────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("🌦️ Weather Advisor • Data source: Open-Meteo API • Storage: MongoDB Atlas")
