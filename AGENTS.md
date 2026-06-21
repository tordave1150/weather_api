# 🌦️ AGENTS.md — Weather & Routing Advisor Dashboard
> **Agentic Build Instructions for AI Coding Agents (Claude Code, Cursor, Copilot, etc.)**
> Read this file top-to-bottom before writing any code. Follow every section in order.

---

## 📌 Project Purpose

Build a **Streamlit dashboard** called **"Weather & Routing Advisor"** that:

1. Fetches daily weather forecasts for **all 77 Thai provinces** from the **Open-Meteo API** (free, no auth key required for basic forecast, but an API key from [open-meteo.com](https://open-meteo.com) is used for higher rate limits and the commercial endpoint).
2. Stores fetched data in **MongoDB Atlas** (Free Tier) as daily audit-trail logs.
3. Displays an **interactive, read-only dashboard** in Streamlit for the Business Operations team.
4. Supports cross-referencing with the internal Utilization Dashboard to trigger **"Unlock Re-route"** decisions.

**Data Privacy Constraint:** No internal team utilization data is ever loaded into this system. This dashboard is weather-only.

---

## 🗂️ Repository Layout

Produce exactly this file structure — no extras unless noted:

```
weather-routing-advisor/
├── .streamlit/
│   └── secrets.toml          # API keys & DB URI — never commit to git
├── data/
│   └── provinces.json        # Static list of 77 provinces with lat/lon
├── etl/
│   └── fetch_weather.py      # Cron/ETL script — fetch & upsert to MongoDB
├── app/
│   ├── main.py               # Streamlit entry point
│   ├── db.py                 # MongoDB connection & query helpers
│   ├── weather.py            # Open-Meteo API client (also used by ETL)
│   └── components/
│       ├── sidebar.py        # Filter controls
│       ├── map_view.py       # Choropleth / marker map
│       ├── table_view.py     # Province data table
│       └── export.py         # CSV / Excel export
├── .gitignore
├── requirements.txt
└── AGENTS.md                 # This file
```

---

## 🔐 Secrets & Configuration (`secrets.toml`)

### File location
`.streamlit/secrets.toml` — **add to `.gitignore` immediately**.

### Template (copy exactly, then fill values)

```toml
# .streamlit/secrets.toml
# ─────────────────────────────────────────────
# Open-Meteo API (commercial endpoint & higher rate limits)
# Sign up at: https://open-meteo.com/en/pricing
[open_meteo]
api_key    = "YOUR_OPEN_METEO_API_KEY"
base_url   = "https://customer-api.open-meteo.com/v1/forecast"
# For the FREE tier (no key needed), set base_url to:
# base_url = "https://api.open-meteo.com/v1/forecast"

# ─────────────────────────────────────────────
# MongoDB Atlas connection
[mongodb]
uri        = "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority"
db_name    = "weather_advisor"
collection = "province_forecasts"
```

### Accessing secrets in Python

```python
import streamlit as st

# Open-Meteo
api_key  = st.secrets["open_meteo"]["api_key"]
base_url = st.secrets["open_meteo"]["base_url"]

# MongoDB
mongo_uri  = st.secrets["mongodb"]["uri"]
db_name    = st.secrets["mongodb"]["db_name"]
collection = st.secrets["mongodb"]["collection"]
```

> **Agent rule:** Never hard-code credentials. Never read from environment variables directly — always use `st.secrets`. Never print or log secrets.

---

## 🌍 Static Province Data (`data/provinces.json`)

Create a JSON array with all **77 Thai provinces**. Each entry:

```json
[
  {
    "province": "Bangkok",
    "region": "Central",
    "lat": 13.7563,
    "lon": 100.5018
  },
  {
    "province": "Chiang Mai",
    "region": "Northern",
    "lat": 18.7883,
    "lon": 98.9853
  }
  // ... all 77 provinces
]
```

**Required fields:** `province` (English name), `region` (one of: `Northern`, `Northeastern`, `Central`, `Eastern`, `Western`, `Southern`), `lat`, `lon`.

Include all 77 provinces. Use official Royal Thai General System romanisation for province names.

---

## 🌐 Open-Meteo API Client (`app/weather.py`)

### Endpoint & Parameters

```
GET https://api.open-meteo.com/v1/forecast
    ?latitude={lat}
    &longitude={lon}
    &daily=precipitation_probability_max,precipitation_sum,weathercode
    &timezone=Asia/Bangkok
    &forecast_days=4
    &apikey={api_key}        # omit if using free tier base_url
```

**`forecast_days=4`** returns today + 3 future days, matching the 3-day forecast schema.

### Rain Level Mapping

Map `precipitation_probability_max` (0–100) to a human-readable level:

| `rain_prob` (%) | `rain_level`   |
|----------------|----------------|
| 0 – 19         | `No Rain`      |
| 20 – 39        | `Light Rain`   |
| 40 – 59        | `Moderate Rain`|
| 60 – 79        | `Heavy Rain`   |
| 80 – 100       | `Very Heavy Rain` |

### Output Shape (per province, per day)

```python
{
    "date": "2025-06-18",           # today (YYYY-MM-DD, Bangkok time)
    "region": "Northern",
    "province": "Chiang Mai",
    "rain_probability": 75,         # today's precipitation_probability_max
    "rain_level": "Heavy Rain",     # mapped from rain_probability
    "rain_volume_mm": 15.5,         # today's precipitation_sum
    "forecast_3_days": [
        {"date": "2025-06-19", "rain_prob": 80, "level": "Very Heavy Rain"},
        {"date": "2025-06-20", "rain_prob": 65, "level": "Heavy Rain"},
        {"date": "2025-06-21", "rain_prob": 40, "level": "Moderate Rain"}
    ],
    "logged_at": "2025-06-18T05:00:00+07:00"   # ISO 8601 with TZ offset
}
```

### Fetch Strategy

- Fetch provinces **sequentially with a 0.1 s sleep** between requests to respect rate limits.
- On HTTP error or timeout, log the error and **skip** that province (do not crash).
- Return a `list[dict]` of all successfully fetched documents.

---

## 🗄️ MongoDB Client (`app/db.py`)

### Connection

```python
from pymongo import MongoClient
import streamlit as st

@st.cache_resource
def get_db():
    client = MongoClient(st.secrets["mongodb"]["uri"])
    db     = client[st.secrets["mongodb"]["db_name"]]
    return db[st.secrets["mongodb"]["collection"]]
```

### Upsert (used by ETL only)

```python
def upsert_forecast(collection, doc: dict):
    """Insert or replace a document for (date, province)."""
    collection.update_one(
        filter={"date": doc["date"], "province": doc["province"]},
        update={"$set": doc},
        upsert=True
    )
```

### Query Helpers (used by dashboard)

```python
def get_forecasts(collection, date: str, regions: list[str] | None = None) -> list[dict]:
    """Return all province docs for a given date, optionally filtered by region."""
    query = {"date": date}
    if regions:
        query["region"] = {"$in": regions}
    return list(collection.find(query, {"_id": 0}).sort("province", 1))


def get_date_range(collection) -> tuple[str, str]:
    """Return (min_date, max_date) of logged data."""
    pipeline = [
        {"$group": {"_id": None, "min": {"$min": "$date"}, "max": {"$max": "$date"}}}
    ]
    result = list(collection.aggregate(pipeline))
    if result:
        return result[0]["min"], result[0]["max"]
    return None, None
```

---

## ⚙️ ETL Script (`etl/fetch_weather.py`)

This script runs as a **daily cron job at 05:00 AM Bangkok time (UTC+7)**.

```
0 22 * * * cd /path/to/project && python etl/fetch_weather.py
```

### Script Logic

```
1. Load provinces.json
2. For each province:
   a. Call weather.py → fetch_province_forecast(province)
   b. Call db.py     → upsert_forecast(collection, doc)
3. Print summary: "Fetched N/77 provinces successfully. Date: YYYY-MM-DD"
4. Exit 0 on success, Exit 1 on fatal error
```

### `secrets.toml` access without Streamlit

When running outside Streamlit (cron), load secrets via `toml`:

```python
import toml, pathlib

secrets = toml.load(pathlib.Path(__file__).parents[1] / ".streamlit/secrets.toml")
mongo_uri  = secrets["mongodb"]["uri"]
api_key    = secrets["open_meteo"]["api_key"]
```

---

## 🖥️ Streamlit Dashboard (`app/main.py`)

### Page Config

```python
st.set_page_config(
    page_title="Weather & Routing Advisor",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER — title + last-updated timestamp + data-date picker  │
├────────────┬────────────────────────────────────────────────┤
│  SIDEBAR   │  MAIN AREA                                      │
│            │  ┌──────────────────────────────────────────┐  │
│  • Date    │  │  KPI CARDS (4 across)                    │  │
│  • Region  │  │  Provinces: 77 | High Rain: N | ...      │  │
│  • Rain    │  ├──────────────────────────────────────────┤  │
│    Level   │  │  MAP VIEW (choropleth by rain_prob)      │  │
│  • Export  │  ├──────────────────────────────────────────┤  │
│            │  │  DATA TABLE (filterable, sortable)       │  │
│            │  ├──────────────────────────────────────────┤  │
│            │  │  3-DAY FORECAST EXPANDER (per province)  │  │
└────────────┴──┴──────────────────────────────────────────┴──┘
```

### KPI Cards

Display four `st.metric` cards in a `st.columns(4)` row:

| Card | Value |
|------|-------|
| Total Provinces | Count of loaded docs |
| High Rain Zones | Count where `rain_probability >= 60` |
| Very Heavy Rain | Count where `rain_level == "Very Heavy Rain"` |
| Avg Rain Prob | Mean `rain_probability` across loaded docs |

### Map View

Use **`pydeck`** (`st.pydeck_chart`) with a `ScatterplotLayer`:
- Marker radius proportional to `rain_probability`.
- Color gradient: green → yellow → orange → red based on `rain_level`.
- Tooltip: province, region, rain_probability, rain_level, rain_volume_mm.

### Data Table

Use `st.dataframe` with these columns (in order):

| Column | Source Field |
|--------|-------------|
| Province | `province` |
| Region | `region` |
| Rain Prob (%) | `rain_probability` |
| Rain Level | `rain_level` |
| Volume (mm) | `rain_volume_mm` |
| Day+1 Prob | `forecast_3_days[0].rain_prob` |
| Day+2 Prob | `forecast_3_days[1].rain_prob` |
| Day+3 Prob | `forecast_3_days[2].rain_prob` |

Apply **colour highlighting** to `rain_probability` column cells:
- `< 40` → light green background
- `40–59` → yellow
- `60–79` → orange
- `>= 80` → red

### Business Rule Indicator Panel

Below the table, add a collapsible `st.expander("📋 Unlock Re-route Eligibility Guide")` that explains:

```
MA Tasks:   Rain zone  +  Team utilization > 85% for 2 consecutive days (Day 0 → Day+1)
Install:    Rain zone  +  Team utilization > 85% for 3 consecutive days (Day+1 → Day+3)

⚠️  Cross-reference rain probability from this dashboard with your internal
    Utilization Dashboard to determine Unlock Re-route eligibility.
```

This is **informational only** — no utilization data is processed here.

### Sidebar Controls (`app/components/sidebar.py`)

```python
# Date picker — bounded to available dates in MongoDB
selected_date = st.sidebar.date_input("📅 Select Date", ...)

# Region multi-select
regions = st.sidebar.multiselect(
    "🗺️ Regions",
    options=["Northern", "Northeastern", "Central", "Eastern", "Western", "Southern"],
    default=[...]   # all selected by default
)

# Rain level filter
rain_levels = st.sidebar.multiselect(
    "🌧️ Rain Level",
    options=["No Rain", "Light Rain", "Moderate Rain", "Heavy Rain", "Very Heavy Rain"],
    default=["Moderate Rain", "Heavy Rain", "Very Heavy Rain"]
)
```

### Export (`app/components/export.py`)

```python
# CSV
st.sidebar.download_button(
    label="⬇️ Export CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name=f"weather_audit_{selected_date}.csv",
    mime="text/csv"
)

# Excel
import io
buffer = io.BytesIO()
df.to_excel(buffer, index=False, engine="openpyxl")
st.sidebar.download_button(
    label="⬇️ Export Excel",
    data=buffer.getvalue(),
    file_name=f"weather_audit_{selected_date}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
```

---

## 📦 Dependencies (`requirements.txt`)

```
streamlit>=1.35.0
pymongo[srv]>=4.6.0
requests>=2.31.0
pandas>=2.2.0
pydeck>=0.9.0
openpyxl>=3.1.0
toml>=0.10.2
```

---

## 🚫 `.gitignore`

```gitignore
# Secrets — never commit
.streamlit/secrets.toml

# Python
__pycache__/
*.pyc
.env
.venv/
venv/

# OS
.DS_Store
Thumbs.db
```

---

## ✅ Agent Checklist (complete in order)

- [ ] Create `.gitignore` with secrets.toml excluded
- [ ] Create `.streamlit/secrets.toml` from template (with placeholder values)
- [ ] Generate `data/provinces.json` with all 77 Thai provinces + lat/lon + region
- [ ] Implement `app/weather.py` — Open-Meteo client + rain level mapper
- [ ] Implement `app/db.py` — MongoDB connection + upsert + query helpers
- [ ] Implement `etl/fetch_weather.py` — standalone cron script (toml-based secrets)
- [ ] Implement `app/components/sidebar.py` — filters
- [ ] Implement `app/components/map_view.py` — pydeck scatter map
- [ ] Implement `app/components/table_view.py` — styled DataFrame
- [ ] Implement `app/components/export.py` — CSV + Excel download buttons
- [ ] Implement `app/main.py` — assemble all components, KPI cards, expander
- [ ] Write `requirements.txt`
- [ ] Verify: no credentials are hard-coded anywhere
- [ ] Verify: `st.cache_resource` wraps the MongoDB connection
- [ ] Verify: ETL script can run standalone (`python etl/fetch_weather.py`) without Streamlit context

---

## 🔒 Security Rules (non-negotiable)

1. **Never** commit `.streamlit/secrets.toml` to version control.
2. **Never** expose `api_key` or `mongo_uri` in Streamlit UI elements, logs, or error messages.
3. The dashboard is **read-only** — no user can write to MongoDB through the Streamlit app.
4. ETL writes are only performed by `etl/fetch_weather.py` running as a server-side cron job.
5. All MongoDB queries use projection `{"_id": 0}` to exclude internal IDs from frontend display.

---

## 🧪 Local Development

```bash
# 1. Clone & install
pip install -r requirements.txt

# 2. Fill in secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with real values

# 3. Seed data (run ETL once)
python etl/fetch_weather.py

# 4. Run dashboard
streamlit run app/main.py
```

---

## 📝 Open-Meteo API Notes

- **Free tier:** `https://api.open-meteo.com/v1/forecast` — no key required, 10,000 calls/day limit.
- **Commercial tier:** `https://customer-api.open-meteo.com/v1/forecast` — requires API key in `secrets.toml`, higher limits, SLA.
- The ETL script makes **77 calls per day** (one per province) — well within the free tier limit.
- Required daily variables: `precipitation_probability_max`, `precipitation_sum`, `weathercode`.
- Always set `timezone=Asia/Bangkok` so date boundaries align with Thai local time.
- Set `forecast_days=4` to get today + 3 future days in a single call.
