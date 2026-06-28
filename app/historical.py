import streamlit as st
import pandas as pd
import io
from datetime import date, timedelta
import sys, os, subprocess

from db import get_historical_rain  # function ใหม่ใน db.py


from theme import apply_theme
apply_theme()

st.markdown(f"""
<div class="hero-banner">
    <div class="hero-left">
        <p class="eyebrow">Thailand Historical Weather</p>
        <h1>🌧 Historical Rain Report</h1>
        <p class="hero-sub">View actual rain data by district based on the selected date and province.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Filters ──
col1, col2, col3 = st.columns([2, 3, 2])

with col1:
    selected_date = st.date_input(
        "📅 Selected Date",
        value=date.today() - timedelta(days=1),
        max_value=date.today(),
    )

# โหลดรายชื่อจังหวัดจาก provinces.json
import json
PROVINCES_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'provinces.json')
with open(PROVINCES_PATH, encoding='utf-8') as f:
    provinces_data = json.load(f)
province_names = sorted([p["province"] for p in provinces_data])

with col2:
    selected_province = st.selectbox(
        "🏙 Select Province",
        options=["All Provinces"] + province_names,
    )

with col3:
    hour_options = ["All Hours"] + [f"{h:02d}:00" for h in range(0, 24)]
    selected_hour = st.selectbox("🕐 Select Time (Hour)", options=hour_options)

# ── Fetch Button ──
col_btn1, col_btn2, _ = st.columns([2, 2, 4])
with col_btn1:
    fetch_now = st.button("Fetch Live Data Now", width="stretch", type="tertiary")
with col_btn2:
    load_report = st.button("Load Report", width="stretch", type="tertiary")

if fetch_now:
    ETL_PATH = os.path.join(os.path.dirname(__file__), '..', 'etl', 'fetch_weather.py')
    with st.spinner("Fetching live data..."):
        try:
            r = subprocess.run(
                [sys.executable, ETL_PATH, "--round", "afternoon"],
                capture_output=True, text=True, timeout=300
            )
            if r.returncode == 0:
                st.success("✅ Fetch complete! Click 'Load Report' to view latest data.")
            else:
                st.error(f"❌ Fetch error: {r.stderr[:300]}")
        except Exception as e:
            st.error(f"❌ {e}")

# ── Load & Display Report ──
if load_report or "rain_df" in st.session_state:
    
    if load_report:
        with st.spinner("Loading data..."):
            df = get_historical_rain(
                selected_date=selected_date,
                province=None if selected_province == "All Provinces" else selected_province,
                hour=None if selected_hour == "All Hours" else int(selected_hour[:2]),
            )
            st.session_state["rain_df"] = df
            st.session_state["rain_meta"] = {
                "date": selected_date, "province": selected_province, "hour": selected_hour
            }
    
    df = st.session_state.get("rain_df", pd.DataFrame())
    
    if not df.empty:
        df = df[df["district"] != "(Province Level)"]
        
    meta = st.session_state.get("rain_meta", {})

    if df.empty:
        st.warning("No data found for the selected criteria.")
    else:
        st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("📍 Locations Found", len(df))
        k2.metric("🌧 Max Rain Volume (mm)", f"{df['precip_sum_mm'].max():.1f}")
        k3.metric("📊 Avg Rain Volume (mm)", f"{df['precip_sum_mm'].mean():.1f}")
        k4.metric("🌡 Max Temperature (°C)", f"{df['temp_max_c'].max():.1f}" if 'temp_max_c' in df else "-")

        st.markdown("---")

        # Chart: top districts by rain volume
        st.markdown("""
        <div class="section-card-header" style="margin-bottom: 16px;">
            <h3>🏆 Top 15 Locations — Rain Volume (mm)</h3>
        </div>
        """, unsafe_allow_html=True)
        top15 = df.nlargest(15, "precip_sum_mm")[["district", "precip_sum_mm"]]
        st.bar_chart(top15.set_index("district")["precip_sum_mm"], color="#42a5f5")

        st.markdown("---")

        # Full table
        st.markdown(f"""
        <div class="section-card-header" style="margin-bottom: 16px;">
            <h3>📋 All Data — {len(df)} records</h3>
        </div>
        """, unsafe_allow_html=True)
        display_cols = ["province", "district", "rain_status", "precip_sum_mm", "temp_max_c", "temp_min_c", "wind_max_kmh", "rainy_hours_detail"]
        display_cols = [c for c in display_cols if c in df.columns]
        
        # Convert rainy_hours_detail list to string for better display in dataframe
        df_display = df[display_cols].copy()
        if "rainy_hours_detail" in df_display.columns:
            df_display["rainy_hours_detail"] = df_display["rainy_hours_detail"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

        def add_emoji(val):
            mapping = {
                "No Rain": "☀️ No Rain",
                "Light Rain": "🌤 Light Rain",
                "Moderate Rain": "🌦 Moderate Rain",
                "Heavy Rain": "🌧 Heavy Rain",
                "Very Heavy Rain": "⛈ Very Heavy Rain",
            }
            return mapping.get(val, val)

        def style_status(val):
            if "No Rain" in str(val): return "color: #8a8f98;"
            elif "Light Rain" in str(val): return "color: #7170ff; font-weight: 500;"
            elif "Moderate Rain" in str(val): return "color: #10b981; font-weight: 500;"
            elif "Heavy Rain" in str(val): return "color: #E89558; font-weight: 500;"
            elif "Very Heavy Rain" in str(val): return "color: #EA2143; font-weight: 600;"
            return ""

        if "rain_status" in df_display.columns:
            df_display["rain_status"] = df_display["rain_status"].apply(add_emoji)

        df_sorted = df_display.sort_values("precip_sum_mm", ascending=False)
        
        # Apply pandas styler if rain_status is present
        if "rain_status" in df_sorted.columns:
            # Use map for pandas >= 2.1.0, otherwise applymap
            styler = df_sorted.style.map(style_status, subset=["rain_status"]) if hasattr(df_sorted.style, "map") else df_sorted.style.applymap(style_status, subset=["rain_status"])
        else:
            styler = df_sorted

        st.dataframe(
            styler,
            width="stretch",
            height=400,
        )

        # ── Export Buttons (sidebar) ──────────────────────────────────────────
        with st.sidebar:
            st.markdown("---")
            st.markdown('<p style="font-size:10px; text-transform:uppercase; letter-spacing:0.5px; color:#6B6A63; margin-bottom:8px;">EXPORT DATA</p>', unsafe_allow_html=True)
            
            csv_bytes = df_display.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            filename_base = f"rain_{meta.get('date', selected_date)}_{(meta.get('province', selected_province) or 'all').replace(' ', '_')}"
            
            st.download_button(
                label="📄 Export CSV (UTF-8)",
                data=csv_bytes,
                file_name=f"{filename_base}.csv",
                mime="text/csv",
                width="stretch",
            )
            
            excel_buf = io.BytesIO()
            with pd.ExcelWriter(excel_buf, engine="xlsxwriter") as writer:
                df_display.to_excel(writer, index=False, sheet_name="Rain Report")
                workbook = writer.book
                worksheet = writer.sheets["Rain Report"]
                header_fmt = workbook.add_format({"bold": True, "bg_color": "#EFF6FF", "font_color": "#1E40AF"})
                for col_num, col_name in enumerate(display_cols):
                    worksheet.write(0, col_num, col_name, header_fmt)
                    worksheet.set_column(col_num, col_num, 18)
            excel_buf.seek(0)
            
            st.download_button(
                label="📊 Export Excel",
                data=excel_buf.read(),
                file_name=f"{filename_base}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
