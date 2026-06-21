"""
Map view component — pydeck ScatterplotLayer for province rain data.
Updated to match redesign spec: new dot colors, light map style.
"""

import streamlit as st
import pydeck as pdk


# Color mapping from spec Section 3.5: rain_level → RGBA
RAIN_COLORS = {
    "No Rain":         [150, 150, 150, 140],     # gray
    "Light Rain":      [29, 158, 117, 160],       # teal
    "Moderate Rain":   [29, 158, 117, 200],       # teal #1D9E75
    "Heavy Rain":      [239, 159, 39, 220],       # amber #EF9F27
    "Very Heavy Rain": [226, 75, 74, 240],        # red #E24B4A
}


def render_map(data: list[dict]):
    """Render a pydeck ScatterplotLayer map of province weather data.

    Args:
        data: List of forecast dicts with lat, lon, rain_probability, rain_level, etc.
    """
    if not data:
        st.info("📍 No data to display on map. Adjust your filters or select a different date.")
        return

    # Enrich each record with color and radius for pydeck
    map_data = []
    for doc in data:
        color = RAIN_COLORS.get(doc.get("rain_level", "No Rain"), [150, 150, 150, 150])
        # Smaller, cleaner dots — radius based on rain level
        level = doc.get("rain_level", "No Rain")
        if level == "Very Heavy Rain":
            radius = 12000
        elif level == "Heavy Rain":
            radius = 10000
        elif level == "Moderate Rain":
            radius = 8000
        else:
            radius = 6000

        map_data.append({
            "lat": doc.get("lat", doc.get("latitude", 13.7563)),
            "lon": doc.get("lon", doc.get("longitude", 100.5018)),
            "province": doc.get("province", ""),
            "region": doc.get("region", ""),
            "rain_probability": doc.get("rain_probability", 0),
            "rain_level": doc.get("rain_level", ""),
            "rain_volume_mm": doc.get("rain_volume_mm", 0),
            "color": color,
            "radius": radius,
        })

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position=["lon", "lat"],
        get_radius="radius",
        get_fill_color="color",
        pickable=True,
        opacity=0.8,
        stroked=True,
        get_line_color=[255, 255, 255, 60],
        line_width_min_pixels=1,
    )

    # Center on Thailand
    view_state = pdk.ViewState(
        latitude=13.0,
        longitude=101.0,
        zoom=5.2,
        pitch=0,
    )

    tooltip = {
        "html": (
            "<b>{province}</b><br/>"
            "Region: {region}<br/>"
            "Rain Probability: {rain_probability}%<br/>"
            "Rain Level: {rain_level}<br/>"
            "Volume: {rain_volume_mm} mm"
        ),
        "style": {
            "backgroundColor": "rgba(26, 26, 26, 0.95)",
            "color": "#E8E6DE",
            "fontSize": "12px",
            "padding": "8px 12px",
            "borderRadius": "8px",
            "border": "0.5px solid rgba(255,255,255,0.1)",
        },
    }

    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip=tooltip,
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        ),
        use_container_width=True,
    )
