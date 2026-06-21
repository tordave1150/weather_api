"""
Map view component — pydeck ScatterplotLayer for province rain data.
"""

import streamlit as st
import pydeck as pdk


# Color mapping: rain_level → RGBA
RAIN_COLORS = {
    "No Rain":         [76, 175, 80, 180],     # green
    "Light Rain":      [205, 220, 57, 180],     # lime/yellow-green
    "Moderate Rain":   [255, 235, 59, 200],     # yellow
    "Heavy Rain":      [255, 152, 0, 210],      # orange
    "Very Heavy Rain": [244, 67, 54, 230],      # red
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
        # Radius proportional to rain_probability (min 3000m, max 25000m)
        prob = doc.get("rain_probability", 0)
        radius = 3000 + (prob / 100) * 22000

        map_data.append({
            "lat": doc.get("lat", doc.get("latitude", 13.7563)),
            "lon": doc.get("lon", doc.get("longitude", 100.5018)),
            "province": doc.get("province", ""),
            "region": doc.get("region", ""),
            "rain_probability": prob,
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
        opacity=0.7,
        stroked=True,
        get_line_color=[255, 255, 255, 100],
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
            "backgroundColor": "rgba(30, 30, 30, 0.9)",
            "color": "white",
            "fontSize": "13px",
            "padding": "8px 12px",
            "borderRadius": "6px",
        },
    }

    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip=tooltip,
            map_style="mapbox://styles/mapbox/dark-v11",
        ),
        use_container_width=True,
    )
