"""
Export component — CSV and Excel download buttons for the sidebar.
"""

import io

import pandas as pd
import streamlit as st


def render_export(data: list[dict], selected_date: str):
    """Render CSV and Excel download buttons in the sidebar.

    Args:
        data: List of forecast dicts.
        selected_date: Date string (YYYY-MM-DD) for the filename.
    """
    if not data:
        return

    # Build flat DataFrame for export
    rows = []
    for doc in data:
        forecast = doc.get("forecast_3_days", [])
        row = {
            "Province": doc.get("province", ""),
            "Region": doc.get("region", ""),
            "Rain Prob (%)": doc.get("rain_probability", 0),
            "Rain Level": doc.get("rain_level", ""),
            "Volume (mm)": doc.get("rain_volume_mm", 0),
            "Day+1 Prob": forecast[0]["rain_prob"] if len(forecast) > 0 else "",
            "Day+1 Level": forecast[0]["level"] if len(forecast) > 0 else "",
            "Day+2 Prob": forecast[1]["rain_prob"] if len(forecast) > 1 else "",
            "Day+2 Level": forecast[1]["level"] if len(forecast) > 1 else "",
            "Day+3 Prob": forecast[2]["rain_prob"] if len(forecast) > 2 else "",
            "Day+3 Level": forecast[2]["level"] if len(forecast) > 2 else "",
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 Export Data")

    # ── CSV download ───────────────────────────────────────────────────
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button(
        label="⬇️ Export CSV",
        data=csv_data,
        file_name=f"weather_audit_{selected_date}.csv",
        mime="text/csv",
    )

    # ── Excel download ─────────────────────────────────────────────────
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    st.sidebar.download_button(
        label="⬇️ Export Excel",
        data=buffer.getvalue(),
        file_name=f"weather_audit_{selected_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
