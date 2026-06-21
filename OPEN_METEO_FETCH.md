# 🌧️ OPEN_METEO_FETCH.md — API Fetch Specification
> **Companion to AGENTS.md** — อ่านไฟล์นี้ก่อนเขียนโค้ดใน `etl/fetch_weather.py` และ `app/weather.py`
> ข้อมูลมาจากการวิเคราะห์ [Open-Meteo Docs](https://open-meteo.com/en/docs) และ [Pricing](https://open-meteo.com/en/pricing) โดยตรง

---

## 1. Free Tier Limits & ความปลอดภัย

| Limit | ค่าจำกัด | การใช้จริงของเรา | % ที่ใช้ |
|-------|----------|-----------------|---------|
| Per minute | 600 calls/min | 77 calls ต่อรอบ (~80 วิ) | ~13% |
| Per hour | 5,000 calls/hr | 77 calls ต่อรอบ | 1.5% |
| Per day | 10,000 calls/day | 154 calls/day (2 รอบ) | **1.5%** |
| Per month | 300,000 calls/month | ~4,620 calls/month | 1.5% |

> ✅ **ปลอดภัยมาก** — ไม่ต้องใช้ API key สำหรับ free tier
> ❌ **ไม่ต้องใส่ `&apikey=`** ใน URL ถ้าใช้ `api.open-meteo.com`
> 🏢 **Commercial tier** (`customer-api.open-meteo.com`) ใช้เมื่อต้องการ SLA + uptime guarantee

---

## 2. Endpoint & URL สมบูรณ์

### Free Tier (ใช้ตัวนี้)
```
GET https://api.open-meteo.com/v1/forecast
```

### Commercial Tier (เมื่อ upgrade)
```
GET https://customer-api.open-meteo.com/v1/forecast?apikey={API_KEY}
```

### Full URL ที่ใช้จริง (ต่อ 1 จังหวัด)
```
https://api.open-meteo.com/v1/forecast
  ?latitude={lat}
  &longitude={lon}
  &daily=precipitation_probability_max,precipitation_sum,rain_sum,showers_sum,weather_code,wind_gusts_10m_max
  &current=weather_code,precipitation,rain
  &timezone=Asia%2FBangkok
  &forecast_days=4
```

> **`forecast_days=4`** = วันนี้ (index 0) + อีก 3 วัน (index 1–3) → ตรงกับ `forecast_3_days` ใน schema

---

## 3. ตัวแปรที่ดึง — เหตุผลทุกตัว

### 3.1 `daily` — แกนหลักของระบบ

| API Field | เก็บใน MongoDB | Unit | เหตุผล |
|-----------|---------------|------|--------|
| `precipitation_probability_max` | `rain_probability` | % | โอกาสฝนสูงสุดของวัน → ใช้ map เป็น `rain_level` |
| `precipitation_sum` | `rain_volume_mm` | mm | ปริมาณน้ำรวมทุกประเภท (rain + showers + snow) → ค่าหลักแสดง UI |
| `rain_sum` | `rain_sum_mm` | mm | ฝนจาก large-scale weather systems เท่านั้น |
| `showers_sum` | `showers_sum_mm` | mm | ฝน convective / ฝนฟ้าคะนองเฉพาะถิ่น ⚠️ **สำคัญมากในไทย** |
| `weather_code` | `weather_code` | WMO | แยกประเภทสภาพอากาศ เช่น thunderstorm vs drizzle |
| `wind_gusts_10m_max` | `wind_gusts_kmh` | km/h | ลมกระโชกสูงสุด → ส่งผลต่อการเดินทาง |

> ⚠️ **ทำไมต้องแยก `rain_sum` กับ `showers_sum`?**
>
> ฝนในไทยช่วงหน้าฝน (พ.ค.–ต.ค.) ส่วนใหญ่เป็น **convective showers** (ฝนฟ้าคะนองเฉพาะถิ่น)
> ถ้าดูแค่ `rain_sum` อาจได้ `0` ทั้งที่ฝนตกหนักจริง เพราะ `rain_sum` จับเฉพาะ
> large-scale frontal rain เท่านั้น → ใช้ `precipitation_sum` เป็นค่าหลักเสมอ

### 3.2 `current` — Live Status บน Dashboard

| API Field | ใช้เพื่อ | หมายเหตุ |
|-----------|---------|---------|
| `weather_code` | แสดงสภาพอากาศ ณ ปัจจุบัน | อิงจาก 15-min model data |
| `precipitation` | ฝนตกอยู่ตอนนี้ (mm ใน 15 นาทีที่แล้ว) | live indicator |
| `rain` | ฝน large-scale ณ ขณะนี้ (mm) | ใช้คู่กับ precipitation |

### 3.3 ❌ ตัวแปรที่ไม่ดึง และเหตุผล

| ตัวแปร | เหตุผลที่ไม่ดึง |
|--------|---------------|
| `hourly=*` | 77 จังหวัด × 24h × 4 วัน = 7,392 data points — ฟุ่มเฟือย use case ต้องการแค่ระดับวัน |
| `temperature_2m_max/min` | ไม่ส่งผล business logic "Unlock Re-route" |
| `uv_index_max` | ไม่เกี่ยวกับการตัดสินใจ re-route |
| `snowfall_sum` | ไม่มีหิมะในไทย |
| `soil_moisture_*` | ไม่เกี่ยวกับ use case |

---

## 4. WMO Weather Code Mapping

ใช้ `weather_code` จาก daily เพื่อแสดง icon และ flag ความเสี่ยง

```python
WMO_DESCRIPTIONS = {
    0:  ("Clear Sky",              "☀️",  "none"),
    1:  ("Mainly Clear",           "🌤️",  "none"),
    2:  ("Partly Cloudy",          "⛅",  "none"),
    3:  ("Overcast",               "☁️",  "none"),
    45: ("Fog",                    "🌫️",  "low"),
    48: ("Rime Fog",               "🌫️",  "low"),
    51: ("Light Drizzle",          "🌦️",  "low"),
    53: ("Moderate Drizzle",       "🌦️",  "low"),
    55: ("Dense Drizzle",          "🌧️",  "medium"),
    61: ("Slight Rain",            "🌧️",  "low"),
    63: ("Moderate Rain",          "🌧️",  "medium"),
    65: ("Heavy Rain",             "🌧️",  "high"),
    80: ("Slight Rain Showers",    "🌦️",  "low"),
    81: ("Moderate Rain Showers",  "🌧️",  "medium"),
    82: ("Violent Rain Showers",   "⛈️",  "high"),
    95: ("Thunderstorm",           "⛈️",  "high"),
    96: ("Thunderstorm + Hail",    "⛈️",  "critical"),
    99: ("Thunderstorm + Heavy Hail","⛈️","critical"),
}

# risk_level: none | low | medium | high | critical
# "high" และ "critical" → ควร highlight บน dashboard และพิจารณา Unlock Re-route
```

---

## 5. Rain Level Mapping (จาก `rain_probability`)

```python
def map_rain_level(rain_prob: int) -> str:
    if rain_prob < 20:
        return "No Rain"
    elif rain_prob < 40:
        return "Light Rain"
    elif rain_prob < 60:
        return "Moderate Rain"
    elif rain_prob < 80:
        return "Heavy Rain"
    else:
        return "Very Heavy Rain"
```

| `rain_probability` (%) | `rain_level` | UI Color |
|------------------------|-------------|----------|
| 0 – 19 | No Rain | `#4CAF50` (green) |
| 20 – 39 | Light Rain | `#FFF176` (yellow) |
| 40 – 59 | Moderate Rain | `#FFB74D` (orange) |
| 60 – 79 | Heavy Rain | `#F44336` (red) |
| 80 – 100 | Very Heavy Rain | `#7B1FA2` (purple) |

---

## 6. MongoDB Document Schema (อัปเดตจาก AGENTS.md)

เพิ่ม field ใหม่ที่ได้จากการวิเคราะห์ API:

```json
{
  "date": "2025-06-18",
  "region": "Northern",
  "province": "Chiang Mai",

  "rain_probability": 75,
  "rain_level": "Heavy Rain",
  "rain_volume_mm": 28.5,

  "rain_sum_mm": 5.2,
  "showers_sum_mm": 23.3,

  "weather_code": 82,
  "weather_desc": "Violent Rain Showers",
  "weather_icon": "⛈️",
  "weather_risk": "high",

  "wind_gusts_kmh": 45.0,

  "current": {
    "weather_code": 81,
    "precipitation_mm": 2.1,
    "rain_mm": 0.5
  },

  "forecast_3_days": [
    {
      "date": "2025-06-19",
      "rain_prob": 80,
      "level": "Very Heavy Rain",
      "precipitation_sum_mm": 35.0,
      "showers_sum_mm": 30.0,
      "weather_code": 95
    },
    {
      "date": "2025-06-20",
      "rain_prob": 65,
      "level": "Heavy Rain",
      "precipitation_sum_mm": 18.0,
      "showers_sum_mm": 15.0,
      "weather_code": 82
    },
    {
      "date": "2025-06-21",
      "rain_prob": 40,
      "level": "Moderate Rain",
      "precipitation_sum_mm": 8.0,
      "showers_sum_mm": 7.0,
      "weather_code": 81
    }
  ],

  "logged_at": "2025-06-18T05:00:00+07:00",
  "fetch_round": "morning"
}
```

> **`fetch_round`**: `"morning"` (05:00) หรือ `"afternoon"` (13:00) — ใช้ trace ว่า record มาจาก model run ไหน

---

## 7. Fetch Schedule (Cron)

### ทำไมถึง Fetch 2 รอบต่อวัน

Weather model อัปเดตตามนี้:
- **GFS (NOAA):** ทุก 1 ชั่วโมง
- **ECMWF:** ทุก 6 ชั่วโมง
- **ICON (DWD):** ทุก 3 ชั่วโมง

Model run ที่ส่งผลต่อ forecast กลางวันไทย:
- **00:00 UTC = 07:00 ไทย** → ดึงรอบเช้า 05:00 ยังไม่ได้ run นี้ แต่ได้ run 18:00 UTC วันก่อน
- **06:00 UTC = 13:00 ไทย** → ได้ model run เช้าที่แม่นที่สุดของวัน

```cron
# รอบเช้า — ETL หลัก, upsert ข้อมูลเริ่มต้นของวัน
0 22 * * *   cd /path/to/project && python etl/fetch_weather.py --round morning

# รอบบ่าย — Refresh จาก model run เช้า (06:00 UTC)
0 6  * * *   cd /path/to/project && python etl/fetch_weather.py --round afternoon
```

> UTC 22:00 = ไทย 05:00 | UTC 06:00 = ไทย 13:00

### Upsert Strategy สำหรับ 2 รอบ

```python
# รอบบ่ายไม่สร้าง document ใหม่ — อัปเดตทับ document เดิมของวันนั้น
collection.update_one(
    filter={"date": doc["date"], "province": doc["province"]},
    update={
        "$set": {
            **doc,
            "fetch_round": round_name,
            "logged_at": datetime.now(tz=TZ_BANGKOK).isoformat(),
        }
    },
    upsert=True
)
```

---

## 8. Python Implementation — `app/weather.py`

```python
import requests
import time
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

TZ_BANGKOK = timezone(timedelta(hours=7))
BASE_URL = "https://api.open-meteo.com/v1/forecast"

DAILY_VARS = ",".join([
    "precipitation_probability_max",
    "precipitation_sum",
    "rain_sum",
    "showers_sum",
    "weather_code",
    "wind_gusts_10m_max",
])

CURRENT_VARS = ",".join([
    "weather_code",
    "precipitation",
    "rain",
])

WMO_MAP = {
    0:  ("Clear Sky",               "☀️",  "none"),
    1:  ("Mainly Clear",            "🌤️",  "none"),
    2:  ("Partly Cloudy",           "⛅",  "none"),
    3:  ("Overcast",                "☁️",  "none"),
    45: ("Fog",                     "🌫️",  "low"),
    48: ("Rime Fog",                "🌫️",  "low"),
    51: ("Light Drizzle",           "🌦️",  "low"),
    53: ("Moderate Drizzle",        "🌦️",  "low"),
    55: ("Dense Drizzle",           "🌧️",  "medium"),
    61: ("Slight Rain",             "🌧️",  "low"),
    63: ("Moderate Rain",           "🌧️",  "medium"),
    65: ("Heavy Rain",              "🌧️",  "high"),
    80: ("Slight Rain Showers",     "🌦️",  "low"),
    81: ("Moderate Rain Showers",   "🌧️",  "medium"),
    82: ("Violent Rain Showers",    "⛈️",  "high"),
    95: ("Thunderstorm",            "⛈️",  "high"),
    96: ("Thunderstorm + Hail",     "⛈️",  "critical"),
    99: ("Thunderstorm + Heavy Hail","⛈️", "critical"),
}


def map_rain_level(rain_prob: int) -> str:
    if rain_prob < 20:   return "No Rain"
    if rain_prob < 40:   return "Light Rain"
    if rain_prob < 60:   return "Moderate Rain"
    if rain_prob < 80:   return "Heavy Rain"
    return "Very Heavy Rain"


def parse_wmo(code: int) -> tuple[str, str, str]:
    """Return (description, icon, risk_level) for a WMO weather code."""
    return WMO_MAP.get(int(code), ("Unknown", "❓", "none"))


def fetch_province_forecast(province: dict, fetch_round: str = "morning") -> dict | None:
    """
    Fetch 4-day daily forecast + current conditions for one province.

    Args:
        province: {"province": str, "region": str, "lat": float, "lon": float}
        fetch_round: "morning" | "afternoon"

    Returns:
        MongoDB document dict, or None on failure.
    """
    params = {
        "latitude":     province["lat"],
        "longitude":    province["lon"],
        "daily":        DAILY_VARS,
        "current":      CURRENT_VARS,
        "timezone":     "Asia/Bangkok",
        "forecast_days": 4,
    }

    try:
        resp = requests.get(BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  ❌ {province['province']}: {e}")
        return None

    daily   = data["daily"]
    current = data.get("current", {})
    today   = daily["time"][0]  # YYYY-MM-DD (Bangkok time, index 0 = today)

    # Today's values (index 0)
    rain_prob    = int(daily["precipitation_probability_max"][0] or 0)
    precip_sum   = float(daily["precipitation_sum"][0] or 0.0)
    rain_sum     = float(daily["rain_sum"][0] or 0.0)
    showers_sum  = float(daily["showers_sum"][0] or 0.0)
    wmo_today    = int(daily["weather_code"][0] or 0)
    wind_gusts   = float(daily["wind_gusts_10m_max"][0] or 0.0)

    wmo_desc, wmo_icon, wmo_risk = parse_wmo(wmo_today)

    # 3-day forecast (index 1, 2, 3)
    forecast_3_days = []
    for i in range(1, 4):
        rp   = int(daily["precipitation_probability_max"][i] or 0)
        wmo  = int(daily["weather_code"][i] or 0)
        _, _, _ = parse_wmo(wmo)  # validate
        forecast_3_days.append({
            "date":               daily["time"][i],
            "rain_prob":          rp,
            "level":              map_rain_level(rp),
            "precipitation_sum_mm": float(daily["precipitation_sum"][i] or 0.0),
            "showers_sum_mm":     float(daily["showers_sum"][i] or 0.0),
            "weather_code":       wmo,
        })

    return {
        "date":             today,
        "region":           province["region"],
        "province":         province["province"],

        "rain_probability": rain_prob,
        "rain_level":       map_rain_level(rain_prob),
        "rain_volume_mm":   precip_sum,

        "rain_sum_mm":      rain_sum,
        "showers_sum_mm":   showers_sum,

        "weather_code":     wmo_today,
        "weather_desc":     wmo_desc,
        "weather_icon":     wmo_icon,
        "weather_risk":     wmo_risk,

        "wind_gusts_kmh":   wind_gusts,

        "current": {
            "weather_code":     int(current.get("weather_code") or 0),
            "precipitation_mm": float(current.get("precipitation") or 0.0),
            "rain_mm":          float(current.get("rain") or 0.0),
        },

        "forecast_3_days":  forecast_3_days,
        "fetch_round":      fetch_round,
        "logged_at":        datetime.now(tz=TZ_BANGKOK).isoformat(),
    }


def fetch_all_provinces(provinces: list[dict], fetch_round: str = "morning",
                        sleep_sec: float = 0.15) -> list[dict]:
    """
    Fetch forecasts for all provinces sequentially.

    sleep_sec=0.15 → 77 provinces ≈ 12 วินาที
    ปลอดภัยต่อ rate limit (600 calls/min = max 10 calls/sec)
    """
    results = []
    total   = len(provinces)

    for i, prov in enumerate(provinces, 1):
        print(f"  [{i:02d}/{total}] {prov['province']} ...", end=" ")
        doc = fetch_province_forecast(prov, fetch_round)
        if doc:
            results.append(doc)
            print(f"✅  rain={doc['rain_probability']}%  {doc['weather_icon']}")
        time.sleep(sleep_sec)

    print(f"\n✅ Fetched {len(results)}/{total} provinces ({fetch_round} round)")
    return results
```

---

## 9. ETL Script — `etl/fetch_weather.py`

```python
#!/usr/bin/env python3
"""
Daily ETL — fetch Open-Meteo forecasts for all 77 Thai provinces → upsert MongoDB.

Usage:
    python etl/fetch_weather.py                    # default: morning round
    python etl/fetch_weather.py --round afternoon  # afternoon refresh
"""

import sys
import json
import argparse
import toml
from pathlib import Path
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta

# ── Path setup ──────────────────────────────────────────────────────────────
ROOT     = Path(__file__).parents[1]
SECRETS  = toml.load(ROOT / ".streamlit/secrets.toml")
PROVINCES_PATH = ROOT / "data/provinces.json"

# ── Import shared weather client ─────────────────────────────────────────────
sys.path.insert(0, str(ROOT))
from app.weather import fetch_all_provinces

TZ_BANGKOK = timezone(timedelta(hours=7))


def get_collection():
    client = MongoClient(SECRETS["mongodb"]["uri"])
    db     = client[SECRETS["mongodb"]["db_name"]]
    return db[SECRETS["mongodb"]["collection"]]


def upsert_all(collection, docs: list[dict]) -> int:
    success = 0
    for doc in docs:
        try:
            collection.update_one(
                filter={"date": doc["date"], "province": doc["province"]},
                update={"$set": doc},
                upsert=True,
            )
            success += 1
        except Exception as e:
            print(f"  ⚠️  Upsert failed for {doc['province']}: {e}")
    return success


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", choices=["morning", "afternoon"], default="morning")
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"🌦️  Weather ETL — {args.round.upper()} ROUND")
    print(f"🕐  {datetime.now(tz=TZ_BANGKOK).strftime('%Y-%m-%d %H:%M:%S')} (Bangkok)")
    print(f"{'='*50}\n")

    # Load province list
    provinces = json.loads(PROVINCES_PATH.read_text(encoding="utf-8"))
    print(f"📍 Loaded {len(provinces)} provinces\n")

    # Fetch from Open-Meteo
    docs = fetch_all_provinces(provinces, fetch_round=args.round)

    if not docs:
        print("❌ No data fetched. Check network or API status.")
        sys.exit(1)

    # Upsert to MongoDB
    print(f"\n📥 Upserting {len(docs)} documents to MongoDB ...")
    collection = get_collection()
    saved = upsert_all(collection, docs)

    print(f"\n{'='*50}")
    print(f"✅  Done: {saved}/{len(docs)} saved  |  Date: {docs[0]['date']}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
```

---

## 10. ตัวอย่าง API Response (สำหรับ Debug)

```json
{
  "latitude": 18.75,
  "longitude": 98.875,
  "timezone": "Asia/Bangkok",
  "timezone_abbreviation": "ICT",
  "utc_offset_seconds": 25200,
  "current": {
    "time": "2025-06-18T13:00",
    "interval": 900,
    "weather_code": 81,
    "precipitation": 1.8,
    "rain": 0.2
  },
  "daily": {
    "time": ["2025-06-18", "2025-06-19", "2025-06-20", "2025-06-21"],
    "precipitation_probability_max": [75, 80, 65, 40],
    "precipitation_sum":             [28.5, 35.0, 18.0, 8.0],
    "rain_sum":                      [5.2,  4.0,  3.0,  1.0],
    "showers_sum":                   [23.3, 31.0, 15.0, 7.0],
    "weather_code":                  [82,   95,   82,   81],
    "wind_gusts_10m_max":            [45.0, 52.0, 38.0, 25.0]
  }
}
```

**สังเกต:** `showers_sum` (23.3 mm) >> `rain_sum` (5.2 mm) → ยืนยันว่าฝนในไทยส่วนใหญ่เป็น convective showers

---

## 11. Checklist สำหรับ Agent

- [ ] ใช้ `api.open-meteo.com` (ไม่ใส่ `apikey`) สำหรับ free tier
- [ ] URL params ตรงตาม section 2 ทุกตัว
- [ ] `forecast_days=4` (ไม่ใช่ 3 หรือ 7)
- [ ] `timezone=Asia/Bangkok` ทุก request — ห้ามลืม
- [ ] เก็บทั้ง `rain_sum` และ `showers_sum` แยกกัน — ไม่ merge
- [ ] `weather_code` map ผ่าน `WMO_MAP` ก่อนเก็บ
- [ ] sleep `0.15s` ระหว่างจังหวัด (~12 วิทั้งหมด)
- [ ] Cron 2 รอบ: `22:00 UTC` (morning) + `06:00 UTC` (afternoon)
- [ ] Upsert filter ใช้ `{date, province}` เสมอ — ไม่ insert ซ้ำ
- [ ] บันทึก `fetch_round` ใน document ทุกครั้ง
