"""
Map view component — pydeck GeoJsonLayer choropleth for province rain data.
FEAT-02: Replaces ScatterplotLayer with colored province polygons.
"""

import json
import pathlib

import streamlit as st
import pydeck as pdk


# Color mapping: rain_level → RGBA (higher alpha for choropleth visibility)
RAIN_COLORS = {
    "No Rain":         [150, 150, 150, 100],     # gray
    "Light Rain":      [29, 158, 117, 160],       # teal
    "Moderate Rain":   [29, 158, 117, 200],       # teal #1D9E75
    "Heavy Rain":      [239, 159, 39, 220],       # amber #EF9F27
    "Very Heavy Rain": [226, 75, 74, 240],        # red #E24B4A
}

# Default color for provinces with no data
NO_DATA_COLOR = [40, 40, 40, 80]


@st.cache_data
def _load_geojson():
    """Load and return Thailand province boundaries GeoJSON (cached)."""
    path = pathlib.Path(__file__).resolve().parent.parent.parent / "data" / "thailand_provinces.geojson"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def _load_name_map():
    """Load GeoJSON → provinces.json name mapping (cached)."""
    path = pathlib.Path(__file__).resolve().parent.parent.parent / "data" / "province_name_map.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_map(data: list[dict]):
    """Render a pydeck GeoJsonLayer choropleth map of province weather data.

    Args:
        data: List of forecast dicts with province, rain_probability, rain_level, etc.
    """
    if not data:
        st.info("📍 No data to display on map. Adjust your filters or select a different date.")
        return

    # Build lookup dicts from forecast data
    level_map = {d["province"]: d.get("rain_level", "No Rain") for d in data}
    prob_map  = {d["province"]: d.get("rain_probability", 0) for d in data}
    vol_map   = {d["province"]: d.get("rain_volume_mm", 0) for d in data}

    # Load GeoJSON and name mapping
    geojson = _load_geojson()
    name_map = _load_name_map()

    # Deep copy features to avoid mutating cached data
    import copy
    geojson_copy = copy.deepcopy(geojson)

    # Inject fill_color into each feature based on rain data
    for feature in geojson_copy["features"]:
        geo_name = feature["properties"].get("NAME_1", "")

        # Skip lake/water features
        if "Lake" in geo_name:
            feature["properties"]["fill_color"] = [0, 0, 0, 0]
            feature["properties"]["rain_level"] = ""
            feature["properties"]["rain_probability"] = ""
            feature["properties"]["rain_volume_mm"] = ""
            feature["properties"]["province_name"] = ""
            continue

        # Map GeoJSON name to canonical province name
        prov_name = name_map.get(geo_name, geo_name)

        rain_level = level_map.get(prov_name, None)
        if rain_level is not None:
            color = RAIN_COLORS.get(rain_level, NO_DATA_COLOR)
        else:
            # Province not in filtered data → show as gray
            color = NO_DATA_COLOR
            rain_level = "No Data"

        feature["properties"]["fill_color"] = color
        feature["properties"]["rain_level"] = rain_level
        feature["properties"]["rain_probability"] = prob_map.get(prov_name, "—")
        feature["properties"]["rain_volume_mm"] = round(vol_map.get(prov_name, 0), 1)
        feature["properties"]["province_name"] = prov_name

    layer = pdk.Layer(
        "GeoJsonLayer",
        data=geojson_copy,
        get_fill_color="properties.fill_color",
        get_line_color=[255, 255, 255, 40],
        line_width_min_pixels=1,
        pickable=True,
        opacity=0.75,
        stroked=True,
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
            "<b>{province_name}</b><br/>"
            "Rain Level: {rain_level}<br/>"
            "Rain Probability: {rain_probability}%<br/>"
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
