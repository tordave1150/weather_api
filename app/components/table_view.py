"""
Data table component with colour-highlighted rain probability cells.
Fixed: uses .map() instead of .applymap() for pandas >= 2.1 compatibility.
FEAT-01: Supports district column when level="district".
"""

import pandas as pd
import streamlit as st


def _rain_prob_color(val):
    """Return CSS background-color for a rain probability value."""
    try:
        v = float(val)
    except (ValueError, TypeError):
        return ""
    if v < 40:
        return "background-color: rgba(29,158,117,0.15); color: #1D9E75;"    # teal
    elif v < 60:
        return "background-color: rgba(239,159,39,0.15); color: #EF9F27;"    # amber
    elif v < 80:
        return "background-color: rgba(239,159,39,0.25); color: #854F0B;"    # dark amber
    else:
        return "background-color: rgba(226,75,74,0.20); color: #E24B4A;"     # red


def _rain_level_badge(val):
    """Return CSS for rain level badge styling."""
    styles = {
        "No Rain": "background-color: rgba(255,255,255,0.05); color: #9C9A92;",
        "Light Rain": "background-color: rgba(29,158,117,0.12); color: #1D9E75;",
        "Moderate Rain": "background-color: #E1F5EE; color: #0F6E56;",
        "Heavy Rain": "background-color: #FAEEDA; color: #854F0B;",
        "Very Heavy Rain": "background-color: #FCEBEB; color: #A32D2D;",
    }
    return styles.get(val, "")


def render_table(data: list[dict], level: str = "province"):
    """Render the data table with coloured rain probability cells.

    Args:
        data: List of forecast dicts.
        level: "province" | "district" — controls which columns to show.
    """
    if not data:
        st.info("📊 No data to display in table. Adjust your filters or select a different date.")
        return

    # Sort by rain_probability descending
    sorted_data = sorted(data, key=lambda x: x.get("rain_probability", 0), reverse=True)

    # Build flat rows
    rows = []
    for doc in sorted_data:
        forecast = doc.get("forecast_3_days", [])
        row = {}

        # Add District column first when in district mode
        if level == "district":
            row["District"] = doc.get("district", "")

        row["Province"] = doc.get("province", "")
        row["Region"] = doc.get("region", "")
        row["Prob %"] = doc.get("rain_probability", 0)
        row["Rain Level"] = doc.get("rain_level", "")
        row["Volume (mm)"] = round(doc.get("rain_volume_mm", 0), 1)
        row["D+1"] = forecast[0]["rain_prob"] if len(forecast) > 0 else "—"
        row["D+2"] = forecast[1]["rain_prob"] if len(forecast) > 1 else "—"
        row["D+3"] = forecast[2]["rain_prob"] if len(forecast) > 2 else "—"

        rows.append(row)

    df = pd.DataFrame(rows)

    # Apply colour styling — use .map() for pandas >= 2.1 compatibility
    prob_columns = ["Prob %", "D+1", "D+2", "D+3"]
    existing_prob_cols = [c for c in prob_columns if c in df.columns]

    try:
        styled = df.style.map(
            _rain_prob_color,
            subset=existing_prob_cols,
        ).map(
            _rain_level_badge,
            subset=["Rain Level"] if "Rain Level" in df.columns else [],
        )
    except AttributeError:
        # Fallback for older pandas — try applymap
        try:
            styled = df.style.applymap(
                _rain_prob_color,
                subset=existing_prob_cols,
            )
        except Exception:
            styled = df

    st.dataframe(
        styled,
        use_container_width=True,
        height=min(500, 40 + len(df) * 35),
        hide_index=True,
    )
