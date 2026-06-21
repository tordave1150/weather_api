"""
Data table component with colour-highlighted rain probability cells.
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
        return "background-color: #c8e6c9; color: #1b5e20;"   # light green
    elif v < 60:
        return "background-color: #fff9c4; color: #f57f17;"   # yellow
    elif v < 80:
        return "background-color: #ffe0b2; color: #e65100;"   # orange
    else:
        return "background-color: #ffcdd2; color: #b71c1c;"   # red


def render_table(data: list[dict]):
    """Render the province data table with coloured rain probability cells.

    Args:
        data: List of forecast dicts.
    """
    if not data:
        st.info("📊 No data to display in table. Adjust your filters or select a different date.")
        return

    # Build flat rows
    rows = []
    for doc in data:
        forecast = doc.get("forecast_3_days", [])
        row = {
            "Province": doc.get("province", ""),
            "Region": doc.get("region", ""),
            "Rain Prob (%)": doc.get("rain_probability", 0),
            "Rain Level": doc.get("rain_level", ""),
            "Volume (mm)": doc.get("rain_volume_mm", 0),
            "Day+1 Prob": forecast[0]["rain_prob"] if len(forecast) > 0 else "—",
            "Day+2 Prob": forecast[1]["rain_prob"] if len(forecast) > 1 else "—",
            "Day+3 Prob": forecast[2]["rain_prob"] if len(forecast) > 2 else "—",
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Apply colour styling to probability columns (fallback if styling not supported)
    try:
        styled = df.style.applymap(
            _rain_prob_color,
            subset=[c for c in prob_columns if c in df.columns],
        )
    except Exception as e:
        # If pandas styling is unavailable, log and use plain dataframe
        st.warning(f"Table styling disabled: {e}")
        styled = df


    st.dataframe(
        styled,
        use_container_width=True,
        height=min(600, 40 + len(df) * 35),
        hide_index=True,
    )
