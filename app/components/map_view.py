"""
Map view component — pydeck GeoJsonLayer choropleth.
Supports both Predicted (Daily) and Current (Real-time) map types,
and both Province and District granularity levels.
"""

import json
import pathlib

import streamlit as st
import pydeck as pdk


# Color mapping: rain_level → RGBA
RAIN_COLORS = {
    "No Rain":         [150, 150, 150, 100],      # gray
    "Light Rain":      [29, 158, 117, 160],       # teal light
    "Moderate Rain":   [29, 158, 117, 200],       # teal #1D9E75
    "Heavy Rain":      [239, 159, 39, 220],       # amber #EF9F27
    "Very Heavy Rain": [226, 75, 74, 240],        # red #E24B4A
}

NO_DATA_COLOR = [40, 40, 40, 80]


@st.cache_data
def _load_geojson(level: str):
    """Load and return GeoJSON boundaries."""
    filename = "thailand_districts.geojson" if level == "district" else "thailand_provinces.geojson"
    path = pathlib.Path(__file__).resolve().parent.parent.parent / "data" / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def _load_name_map(level: str):
    """Load GeoJSON → canonical name mapping."""
    filename = "district_name_map.json" if level == "district" else "province_name_map.json"
    path = pathlib.Path(__file__).resolve().parent.parent.parent / "data" / filename
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_current_rain_level(mm: float) -> str:
    """Map current precipitation_mm to a categorical level for consistent coloring."""
    if mm == 0:     return "No Rain"
    if mm < 2.5:    return "Light Rain"
    if mm < 10.0:   return "Moderate Rain"
    if mm < 50.0:   return "Heavy Rain"
    return "Very Heavy Rain"


def render_map(data: list[dict], level: str = "province", map_type: str = "predicted"):
    """Render a pydeck GeoJsonLayer choropleth map.

    Args:
        data: List of forecast dicts.
        level: "province" | "district"
        map_type: "predicted" (Daily aggregated) | "current" (Real-time snapshot)
    """
    if not data:
        st.info("📍 No data to display on map.")
        return

    # Determine key mapping
    id_key = "district" if level == "district" else "province"
    geo_name_key = "amp_en" if level == "district" else "NAME_1"

    # Build lookup dicts
    lookup = {}
    for d in data:
        loc_name = d.get(id_key, "")
        if not loc_name:
            continue
            
        if map_type == "current":
            current_data = d.get("current", {})
            precip_mm = float(current_data.get("precipitation_mm", 0.0))
            r_level = _get_current_rain_level(precip_mm)
            lookup[loc_name] = {
                "rain_level": r_level,
                "display_val": f"{precip_mm} mm/h",
                "label": "Current Rain Rate"
            }
        else:
            r_level = d.get("rain_level", "No Rain")
            prob = d.get("rain_probability", 0)
            vol = round(d.get("rain_volume_mm", 0), 1)
            lookup[loc_name] = {
                "rain_level": r_level,
                "display_val": f"{prob}% (Vol: {vol} mm)",
                "label": "Daily Prediction"
            }

    geojson = _load_geojson(level)
    name_map = _load_name_map(level)

    # Deep copy features to avoid mutating cache
    import copy
    geojson_copy = copy.deepcopy(geojson)

    for feature in geojson_copy["features"]:
        geo_name = feature["properties"].get(geo_name_key, "")

        if "Lake" in geo_name:
            feature["properties"]["fill_color"] = [0, 0, 0, 0]
            feature["properties"]["rain_level"] = ""
            feature["properties"]["display_val"] = ""
            feature["properties"]["loc_name"] = ""
            continue

        # Map GeoJSON name to canonical name
        canonical_name = name_map.get(geo_name, geo_name)
        
        info = lookup.get(canonical_name)
        if info:
            color = RAIN_COLORS.get(info["rain_level"], NO_DATA_COLOR)
            feature["properties"]["rain_level"] = info["rain_level"]
            feature["properties"]["display_val"] = info["display_val"]
            feature["properties"]["label"] = info["label"]
        else:
            color = NO_DATA_COLOR
            feature["properties"]["rain_level"] = "No Data"
            feature["properties"]["display_val"] = "—"
            feature["properties"]["label"] = "Status"

        feature["properties"]["fill_color"] = color
        feature["properties"]["loc_name"] = canonical_name

    layer = pdk.Layer(
        "GeoJsonLayer",
        data=geojson_copy,
        get_fill_color="properties.fill_color",
        get_line_color=[255, 255, 255, 40] if level == "province" else [255, 255, 255, 10],
        line_width_min_pixels=1 if level == "province" else 0,
        pickable=True,
        opacity=0.75,
        stroked=True,
    )

    view_state = pdk.ViewState(
        latitude=13.0,
        longitude=101.0,
        zoom=5.0,
        pitch=0,
    )

    tooltip = {
        "html": (
            "<b>{loc_name}</b><br/>"
            "Level: {rain_level}<br/>"
            "{label}: {display_val}"
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
