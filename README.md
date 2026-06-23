# ⛈ Weather Advisor — Hyper-Local Thailand Weather Intelligence

**Weather Advisor** is a professional, interactive weather dashboard built to support business operations, logistics, and risk management across Thailand. It provides hyper-local weather intelligence covering 77 provinces and over 900+ districts, empowering teams to track real-time conditions and predict weather impacts up to 3 days in advance.

---

## 🌟 Key Business Value

- **Hyper-Local Precision (District-Level):** Move beyond broad provincial data. Drill down into 913 specific districts to accurately plan logistics, agricultural activities, or outdoor operations.
- **Real-Time vs. Predicted Validation:** Instantly compare the **Daily Predicted Risk** alongside the **Real-Time Current Rain** through intuitive side-by-side maps.
- **Instant Risk Assessment:** A 3-day forward-looking forecast utilizing clear, traffic-light color coding (Green/Amber/Red) allows executives and operational teams to spot severe weather risks at a glance without reading complex data.
- **Seamless Data Integration:** Filter data visually and export it directly to **CSV** or **Excel** with one click for easy integration into your existing Business Intelligence (BI) or reporting tools.

---

## 💻 Product Features & UI Overview

```text
┌─────────────────────────────────────────────────────────────┐
│  Filters (Sidebar)         │   Executive Dashboard          │
│  • Toggle: Province/Dist.  │   • KPIs & Alert Banners       │
│  • Select Date             │   • Dual Map Views (Side-by-Side)│
│  • Region Selection        │     - Daily Predicted Risk     │
│  • Risk Level Filter       │     - Real-Time Rain Rate      │
│  • Export (Excel/CSV)      │   • Color-Coded 3-Day Forecast │
└─────────────────────────────────────────────────────────────┘
```

### 1. Executive KPIs & Alerts
Top-level metrics give a rapid overview of the current national weather status. 
- **High Rain Zones:** Counts areas with a rain probability over 40%.
- **Very Heavy Rain:** Counts critical areas expecting severe storms.
- **Automated Alerts:** A critical warning banner automatically appears if more than 10 locations are facing "Very Heavy Rain."

### 2. Dual Map Analysis
Two Choropleth maps rendered side-by-side for instant gap analysis:
- 🗺️ **Predicted Daily Rain Map:** Colors areas based on the *maximum probability* of rain for the day. Excellent for forward planning.
- 📡 **Current Rain Map (Latest Refresh):** Colors areas based on the *exact real-time rain volume (mm)* currently falling. Excellent for live operational tracking.

### 3. Visual 3-Day Forecast
A comprehensive timeline organized by region. Instead of reading through data tables, Day+1, Day+2, and Day+3 cards are dynamically colored (Red for Severe, Amber for Heavy, Green for Moderate) so decision-makers can scan trends in seconds.

---

## 🚦 Risk Level Classification

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

- **Data Source:** [Open-Meteo API](https://open-meteo.com/) (Free Tier).
- **Automated ETL Pipeline:** A Python script (`etl/fetch_weather.py`) fetches, cleans, and structures data twice a day (5:00 AM and 1:00 PM ICT).
- **Cloud Database:** MongoDB Atlas securely stores the historical and forecasted data.
- **CI/CD Automation:** GitHub Actions automatically runs the ETL pipeline on a cron schedule without manual intervention.
- **Frontend Framework:** Built on Streamlit, optimized for data applications.

### 🔄 ETL Workflow (GitHub Actions)
| Round | Local Time (ICT) | Purpose |
|---|---|---|
| **Morning** | 05:00 | Establishes the baseline prediction for the day's operations. |
| **Afternoon** | 13:00 | Incorporates updated meteorological models to refine the afternoon/evening outlook. |

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
   collection = "forecasts"
   ```
4. Run the application: 
   ```bash
   streamlit run app/main.py
   ```

### Running the ETL Manually
```bash
# Fetch province-level data
python etl/fetch_weather.py --level province

# Fetch district-level data (takes longer due to 900+ locations)
python etl/fetch_weather.py --level district
```

*Note: When deploying or running ETL via CI/CD (like GitHub Actions), ensure that the MongoDB Atlas Network Access allows connections from `0.0.0.0/0` as CI runners use dynamic IP addresses.*

---

*Disclaimer: Weather data is sourced from meteorological models and represents probabilities. Accuracy varies, especially for D+2 and D+3 forecasts.*
