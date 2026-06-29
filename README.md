# ⛈ Weather Advisor — Hyper-Local Thailand Weather Intelligence

**Weather Advisor** is a professional, interactive weather dashboard built to support business operations, logistics, and risk management across Thailand. It provides hyper-local weather intelligence covering **77 provinces** and **913 districts**. It features both **Future Forecasts** and **Historical Analysis**, empowering teams to track real-time conditions, predict weather impacts up to 3 days in advance, and audit past weather events.

---

## 🌟 Key Business Value

- **Hyper-Local Precision (District-Level):** Move beyond broad provincial data. Drill down into 913 specific districts to accurately plan logistics, agricultural activities, or analyze past weather events.
- **Dual Perspective:** Combine **3-Day Forward-Looking Forecasts** with **Historical Rain Auditing** to make well-rounded operational decisions.
- **Visual Intelligence:** Intuitive UI with traffic-light color coding (Green/Amber/Red) for risks and side-by-side maps for instant gap analysis.
- **Seamless Data Integration:** Filter data visually and export it directly to **CSV** or **Excel** with one click for easy integration into your existing BI or reporting tools.

---

## 💻 Product Features & UI Overview

The application is divided into two primary dashboards:

### 1. 🌤 Weather Forecast Dashboard
*Focus: Risk prevention and forward planning (Up to 3 Days)*

- **Executive KPIs & Alerts:** Real-time counters for High Rain Zones and Very Heavy Rain. Automated warning banners appear if critical thresholds are met.
- **Dual Map Analysis:** Two maps rendered side-by-side.
  - 🗺️ **Predicted Daily Rain Map:** Max probability of rain for the day.
  - 📡 **Current Rain Map:** Real-time exact rain volume (mm) falling.
- **Visual 3-Day Forecast:** Dynamic, color-coded timeline (Day+1, Day+2, Day+3) organized by region for rapid scanning.
- **Manual Refresh Button:** Fetches Province then District data sequentially with a live progress bar. Province timeout: 300s. District timeout: 600s.

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

| Component | Detail |
|-----------|--------|
| **Data Source** | [Open-Meteo API](https://open-meteo.com/) (Free Tier) — Forecast API + Archive API |
| **ETL Scripts** | `etl/fetch_weather.py` (forecast), `etl/backfill.py` (historical) |
| **Database** | MongoDB Atlas — upsert keyed on `{date, province/district, level}` |
| **Automation** | GitHub Actions cron — 08:00 & 13:00 Bangkok time |
| **Frontend** | Streamlit + custom CSS (Sky Palette light theme) |

### ETL Rate Limiting & Retry Config (`app/weather.py`)

| Parameter | Value | Notes |
|-----------|-------|-------|
| `sleep_sec` | 0.3s | Delay between requests |
| `timeout` | 5s | Per HTTP request |
| `max_retries` | 2 | Retry on error before skipping |
| Retry delay (attempt 0) | 3s | Down from 15s for faster recovery |

### Estimated ETL Runtime

| Level | Locations | Estimated Time |
|-------|-----------|----------------|
| Province | 77 | ~4 min |
| District | 913 | ~35 min |
| **Total (both)** | **990** | **~39 min** |

---

## 🤖 GitHub Actions Automation

Workflow file: `.github/workflows/etl.yml`

```
Cron Schedule (UTC):
  01:00 UTC → Morning round  (08:00 BKK)
  06:00 UTC → Afternoon round (13:00 BKK)
```

**Scheduled (Cron) runs:** fetch Province → then District automatically.  
**Manual (workflow_dispatch) runs:** select level (province / district) individually.

```yaml
timeout-minutes: 45   # covers both province + district in one job
```

> **MongoDB upsert key:** `{date, province, level}` for provinces and `{date, district, level}` for districts — pressing Refresh multiple times on the same day will **UPDATE**, never duplicate.

---

## 🚀 Setup & Deployment

### Local Development

1. Clone the repository and activate your Python environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
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
# Province-level forecast (77 locations, ~4 min)
python etl/fetch_weather.py --round morning --level province

# District-level forecast (913 locations, ~35 min)
python etl/fetch_weather.py --round morning --level district

# Historical backfill
python etl/backfill.py --level district --days 7
```

### GitHub Actions — First-Time Setup

1. Go to **Settings → Secrets and variables → Actions** and add:
   - `MONGODB_URI`
   - `MONGODB_DB_NAME`
   - `MONGODB_COLLECTION`
2. Go to **Actions tab** → enable workflows if prompted.
3. Trigger a manual run: `Actions → Weather ETL → Run workflow`.

> **Note:** MongoDB Atlas Network Access must allow `0.0.0.0/0` for GitHub Actions runners (dynamic IPs).

---

*Disclaimer: Weather data is sourced from meteorological models and represents probabilities. Accuracy varies, especially for D+2 and D+3 forecasts.*
