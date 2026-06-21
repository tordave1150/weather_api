"""
Sidebar filter controls for the Weather Advisor dashboard.
"""

from datetime import datetime, date

import streamlit as st

from db import get_date_range

ALL_REGIONS = ["Northern", "Northeastern", "Central", "Eastern", "Western", "Southern"]
ALL_RAIN_LEVELS = ["No Rain", "Light Rain", "Moderate Rain", "Heavy Rain", "Very Heavy Rain"]


def render_sidebar(collection, available_provinces: list[str]) -> dict:
    """Render sidebar filters and return selected filter values.

    Args:
        collection: PyMongo collection object.

    Returns:
        Dict with keys: 'selected_date', 'regions', 'rain_levels'.
    """
    st.sidebar.header("🔍 Filters")

    # ── Date picker — bounded to available dates in MongoDB ────────────
    min_date_str, max_date_str = get_date_range(collection)

    if min_date_str and max_date_str:
        min_date = datetime.strptime(min_date_str, "%Y-%m-%d").date()
        max_date = datetime.strptime(max_date_str, "%Y-%m-%d").date()
    else:
        # No data yet — default to today
        min_date = date.today()
        max_date = date.today()

    selected_date = st.sidebar.date_input(
        "📅 Select Date",
        value=max_date,
        min_value=min_date,
        max_value=max_date,
    )

    # ── Region multi-select ────────────────────────────────────────────
    regions = st.sidebar.multiselect(
        "🗺️ Regions",
        options=ALL_REGIONS,
        default=ALL_REGIONS,
    )

    # ── Rain level filter ──────────────────────────────────────────────
    rain_levels = st.sidebar.multiselect(
        "🌧️ Rain Level",
        options=ALL_RAIN_LEVELS,
        default=["Moderate Rain", "Heavy Rain", "Very Heavy Rain"],
    )

    # ── Province filter ────────────────────────────────────────────────
    selected_provinces = st.sidebar.multiselect(
        "📍 Provinces",
        options=available_provinces,
        default=[],
        help="Leave empty to show all provinces in selected regions"
    )

    return {
        "selected_date": selected_date.strftime("%Y-%m-%d") if isinstance(selected_date, date) else str(selected_date),
        "regions": regions,
        "rain_levels": rain_levels,
        "provinces": selected_provinces,
    }
