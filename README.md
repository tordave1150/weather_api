# ⛈ Weather Advisor — Hyper-Local Thailand Weather Intelligence

**Weather Advisor** is a professional, interactive weather dashboard built to support business operations, logistics, and risk management across Thailand. It provides hyper-local weather intelligence covering 77 provinces and over 900+ districts. It features both **Future Forecasts** and **Historical Analysis**, empowering teams to track real-time conditions, predict weather impacts up to 3 days in advance, and audit past weather events.

---

## 🌟 Key Business Value

- **Hyper-Local Precision (District-Level):** Move beyond broad provincial data. Drill down into 913 specific districts to accurately plan logistics, agricultural activities, or analyze past weather events.
- **Dual Perspective:** Combine **3-Day Forward-Looking Forecasts** with **Historical Rain Auditing** to make well-rounded operational decisions.
- **Visual Intelligence:** Intuitive UI with traffic-light color coding (Green/Amber/Red) for risks and side-by-side maps for instant gap analysis.
- **Seamless Data Integration:** Filter data visually and export it directly to **CSV** or **Excel** with one click for easy integration into your existing Business Intelligence (BI) or reporting tools.

---

## 💻 Product Features & UI Overview

The application is divided into two primary dashboards:

### 1. 🌤 Weather Forecast Dashboard
*Focus: Risk prevention and forward planning (Up to 3 Days)*

- **Executive KPIs & Alerts:** Real-time counters for High Rain Zones and Very Heavy Rain. Automated warning banners appear if critical thresholds are met.
- **Dual Map Analysis:** Two Choropleth maps rendered side-by-side.
  - 🗺️ **Predicted Daily Rain Map:** Max probability of rain for the day.
  - 📡 **Current Rain Map:** Real-time exact rain volume (mm) falling.
- **Visual 3-Day Forecast:** Dynamic, color-coded timeline (Day+1, Day+2, Day+3) organized by region for rapid scanning.

### 2. 🌧 Historical Rain Report (Audit Dashboard)
*Focus: Post-event analysis and claims validation*

- **Historical Data Retrieval:** Select any past date and province to retrieve exact rain data (volume, temperature, wind speed, and hourly rain details).
- **Live Data Fetching:** On-demand data fetching capability directly from the UI to backfill missing historical records.
- **Top Impacted Areas:** Automatic Bar Chart highlighting the Top 15 areas with the highest rainfall volume.
- **Detailed Data Grid:** Interactive table displaying comprehensive weather metrics, ready for export.

---

## 🚦 Risk Level Classification (Forecasts)

Weather Advisor automatically categorizes risk to simplify decision-making.

| Probability | Rain Level | Actionable Insight | Color Coding |
|---|---|---|---|
| **< 20%** | No Rain | Safe for all outdoor operations. | ⬜ Gray / Transparent |
| **20–39%** | Light Rain | Minor disruptions possible. | 🔵 Blue / Info |
| **40–59%** | Moderate Rain | Prepare for moderate delays. | 🟢 Green / Safe |
| **60–79%** | Heavy Rain | High risk of logistical delays. | 🟠 Amber / Warning |
| **≥ 80%** | Very Heavy Rain | Critical risk. Potential flooding. | 🔴 Red / Danger |

---

## ⚙️ Technical Architecture & Data Pipeline

The platform is designed to be highly automated and maintenance-free, leveraging modern cloud infrastructure.

- **Data Source:** [Open-Meteo API](https://open-meteo.com/) (Free Tier) - specifically using the Forecast API and the Archive API for historical backfills.
- **Automated ETL Pipeline:** Python scripts (`etl/fetch_weather.py` and `etl/backfill.py`) fetch, clean, and structure data.
- **Cloud Database:** MongoDB Atlas securely stores the historical and forecasted data in separate collections.
- **CI/CD Automation:** GitHub Actions automatically runs the ETL pipeline on a cron schedule without manual intervention.
- **Frontend Framework:** Built on Streamlit, leveraging a custom CSS design system (Linear-inspired dark theme).

---

## 🚀 Setup & Deployment for Developers

### Local Development
1. Clone the repository and activate your Python environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Create `.streamlit/secrets.toml` with your MongoDB credentials:
   ```toml
   [mongodb]
   uri        = "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/"
   db_name    = "weather_db"
   ```
4. Run the application: 
   ```bash
   streamlit run app/main.py
   ```

### Running the ETL Manually
```bash
# Fetch live forecast data (province-level)
python etl/fetch_weather.py --level province

# Fetch historical data for the last 7 days (district-level)
python etl/backfill.py --level district --days 7
```

*Note: When deploying or running ETL via CI/CD (like GitHub Actions), ensure that the MongoDB Atlas Network Access allows connections from `0.0.0.0/0` as CI runners use dynamic IP addresses.*

---

*Disclaimer: Weather data is sourced from meteorological models and represents probabilities. Accuracy varies, especially for D+2 and D+3 forecasts.*
