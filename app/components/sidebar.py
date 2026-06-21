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
        available_provinces: Sorted list of all province names.

    Returns:
        Dict with keys: 'selected_date', 'regions', 'rain_levels', 'province_search'.
    """
    with st.sidebar:
        # ── Logo row ──────────────────────────────────────────────────
        st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:20px; padding: 4px 0;">
            <div style="
                width:26px; height:26px;
                background:#1D9E75;
                border-radius:7px;
                display:flex; align-items:center; justify-content:center;
                font-size:14px; color:white;
            ">⛈</div>
            <span style="font-size:14px; font-weight:500; color:var(--color-text-primary, #E8E6DE);">Weather Advisor</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Date picker ───────────────────────────────────────────────
        st.markdown('<p style="font-size:10px; text-transform:uppercase; letter-spacing:0.5px; color:#6B6A63; margin-bottom:4px;">DATE</p>', unsafe_allow_html=True)

        min_date_str, max_date_str = get_date_range(collection)
        if min_date_str and max_date_str:
            min_date = datetime.strptime(min_date_str, "%Y-%m-%d").date()
            max_date = datetime.strptime(max_date_str, "%Y-%m-%d").date()
        else:
            min_date = date.today()
            max_date = date.today()

        selected_date = st.date_input(
            "📅 Select Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            label_visibility="collapsed",
        )

        # ── Region multi-select ───────────────────────────────────────
        st.markdown('<p style="font-size:10px; text-transform:uppercase; letter-spacing:0.5px; color:#6B6A63; margin: 16px 0 4px 0;">REGION</p>', unsafe_allow_html=True)
        regions = st.multiselect(
            "🗺️ Regions",
            options=ALL_REGIONS,
            default=ALL_REGIONS,
            label_visibility="collapsed",
        )

        # ── Rain level filter ─────────────────────────────────────────
        st.markdown('<p style="font-size:10px; text-transform:uppercase; letter-spacing:0.5px; color:#6B6A63; margin: 16px 0 4px 0;">RAIN LEVEL</p>', unsafe_allow_html=True)
        rain_levels = st.multiselect(
            "🌧️ Rain Level",
            options=ALL_RAIN_LEVELS,
            default=["Moderate Rain", "Heavy Rain", "Very Heavy Rain"],
            label_visibility="collapsed",
        )

        # ── Province search ───────────────────────────────────────────
        st.markdown('<p style="font-size:10px; text-transform:uppercase; letter-spacing:0.5px; color:#6B6A63; margin: 16px 0 4px 0;">PROVINCE</p>', unsafe_allow_html=True)
        province_search = st.text_input(
            "🔍 Filter province",
            placeholder="Filter province...",
            label_visibility="collapsed",
        )

    return {
        "selected_date": selected_date.strftime("%Y-%m-%d") if isinstance(selected_date, date) else str(selected_date),
        "regions": regions,
        "rain_levels": rain_levels,
        "province_search": province_search,
    }
