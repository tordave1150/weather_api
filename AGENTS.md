# AGENTS.md — Weather Advisor

คู่มือสำหรับ AI agent หรือ developer ที่ต้องการทำความเข้าใจโครงสร้างและข้อกำหนดของ project นี้ก่อนลงมือแก้ไข

---

## Project Overview

**Weather Advisor** คือ Streamlit dashboard แสดงข้อมูลพยากรณ์อากาศรายวันของ 77 จังหวัดไทย
- **Live app**: https://weatheradvisor.streamlit.app/
- **Data source**: Open-Meteo API (free tier, ไม่ต้องใช้ API key)
- **Storage**: MongoDB Atlas — upsert key คือ `(date, province)`
- **ETL**: `etl/fetch_weather.py` — รันวันละ 2 รอบผ่าน Cron (05:00 และ 13:00 เวลาไทย)

---

## Repository Structure

```
weather_api/
├── app/
│   ├── main.py                  # Streamlit entry point — layout, KPIs, hero, 3-day section
│   ├── db.py                    # MongoDB helpers: get_db(), get_forecasts(), upsert_forecast()
│   ├── weather.py               # Open-Meteo client: fetch_province_forecast(), map_rain_level()
│   └── components/
│       ├── map_view.py          # pydeck ScatterplotLayer map
│       ├── sidebar.py           # Sidebar filters (date, region, rain level, province search)
│       ├── table_view.py        # Styled DataFrame table
│       └── export.py            # CSV/Excel download buttons
├── data/
│   └── provinces.json           # 77 จังหวัด: {province, region, lat, lon}
├── etl/
│   └── fetch_weather.py         # CLI ETL script — fetch + upsert to MongoDB
└── requirements.txt
```

---

## Data Model (MongoDB Document)

แต่ละ document ใน MongoDB มี schema ดังนี้:

```json
{
  "date": "2025-06-23",
  "province": "Chiang Mai",
  "region": "Northern",
  "lat": 18.7883,
  "lon": 98.9853,

  "rain_probability": 75,
  "rain_level": "Heavy Rain",
  "rain_volume_mm": 12.4,
  "rain_sum_mm": 11.0,
  "showers_sum_mm": 1.4,

  "weather_code": 63,
  "weather_desc": "Moderate Rain",
  "weather_icon": "🌧️",
  "weather_risk": "medium",
  "wind_gusts_kmh": 28.5,

  "current": {
    "weather_code": 61,
    "precipitation_mm": 2.1,
    "rain_mm": 2.0
  },

  "forecast_3_days": [
    { "date": "2025-06-24", "rain_prob": 60, "level": "Moderate Rain", "precipitation_sum_mm": 8.2, "showers_sum_mm": 0.9, "weather_code": 61 },
    { "date": "2025-06-25", "rain_prob": 45, "level": "Moderate Rain", "precipitation_sum_mm": 5.0, "showers_sum_mm": 0.5, "weather_code": 80 },
    { "date": "2025-06-26", "rain_prob": 20, "level": "Light Rain",    "precipitation_sum_mm": 1.5, "showers_sum_mm": 0.2, "weather_code": 51 }
  ],

  "fetch_round": "morning",
  "logged_at": "2025-06-23T05:12:34+07:00"
}
```

### Rain Level Classification

| `rain_probability` | `rain_level`     |
|--------------------|------------------|
| < 20%              | No Rain          |
| 20–39%             | Light Rain       |
| 40–59%             | Moderate Rain    |
| 60–79%             | Heavy Rain       |
| ≥ 80%              | Very Heavy Rain  |

> ค่านี้คำนวณใน `app/weather.py → map_rain_level()` และเก็บลง MongoDB — ไม่ได้มาจาก API โดยตรง

---

## Pending Business Feedback (3 รายการ)

> **สถานะ**: รอ implementation — ต้องทำทั้ง 3 ข้อใน sprint นี้

---

### [FEAT-01] เพิ่มความละเอียดข้อมูลระดับอำเภอ (District-level Granularity)

**Business requirement**: ต้องการดูข้อมูลพยากรณ์ในระดับอำเภอ ไม่ใช่แค่จังหวัด

**Decision**: ระดับอำเภอ (district) เหมาะสมเพียงพอ — granular กว่าจังหวัดโดยไม่ overload UX เหมือนระดับตำบล

#### สิ่งที่ต้องทำ

**1. เพิ่มไฟล์ข้อมูลอำเภอ**

เตรียมไฟล์ `data/districts.json` ในรูปแบบ:

```json
[
  {
    "district": "Mueang Chiang Mai",
    "province": "Chiang Mai",
    "region": "Northern",
    "lat": 18.7883,
    "lon": 98.9853
  },
  ...
]
```

- ต้องมีฟิลด์ `district`, `province`, `region`, `lat`, `lon`
- ใช้พิกัดศูนย์กลางของอำเภอ (ถ้าไม่มีข้อมูลพิกัดแม่นยำ สามารถประมาณจากพิกัดจังหวัดบวก offset เล็กน้อย)
- ไทยมี ~928 อำเภอ — พิจารณา pagination หรือ filter บังคับก่อน load

**2. แก้ไข ETL (`etl/fetch_weather.py`)**

- เพิ่ม `--level` argument: `python etl/fetch_weather.py --level district`
- โหลด `data/districts.json` แทน `data/provinces.json` เมื่อ `level=district`
- Document schema เพิ่มฟิลด์ `district` และ `level: "district" | "province"`
- upsert key เปลี่ยนเป็น `(date, district)` สำหรับ level district

**3. แก้ไข MongoDB query (`app/db.py`)**

```python
def get_forecasts(collection, date, regions=None, level="province"):
    query = {"date": date, "level": level}
    if regions:
        query["region"] = {"$in": regions}
    return list(collection.find(query, {"_id": 0}).sort("district" if level == "district" else "province", 1))
```

**4. แก้ไข Sidebar (`app/components/sidebar.py`)**

- เพิ่ม toggle: `st.radio("Granularity", ["Province", "District"], horizontal=True)`
- เมื่อเลือก District ให้แสดง province filter แทน free-text search (เพื่อ scope ให้แคบลงก่อน)

**5. แก้ไข `app/main.py`**

- รับ `level` จาก sidebar filters
- ส่ง `level` ไปยัง `get_forecasts()`
- ส่วน 3-Day Forecast: group by `district` แทน province เมื่ออยู่ใน district mode
- KPI cards: ปรับ label เป็น "Total Districts" แทน "Total Provinces"

**6. แก้ไข Table (`app/components/table_view.py`)**

- เพิ่มคอลัมน์ `District` และ `Province` เมื่ออยู่ใน district mode
- เรียงลำดับ: province ก่อน จากนั้น district ภายใน province

**Rate limit note**: 928 อำเภอ × 0.15s delay ≈ ~2.5 นาที/รอบ — ยังอยู่ใน free tier ของ Open-Meteo (600 calls/min)

---

### [FEAT-02] แผนที่แสดงพื้นที่ระบายสี (Choropleth Map แทน Scatter Dots)

**Business requirement**: จุดบนแผนที่ควรระบายเต็มพื้นที่จังหวัด/อำเภอ แทนการใช้จุดกลม

**ไฟล์ที่ต้องแก้**: `app/components/map_view.py`

#### วิธีที่แนะนำ: GeoJsonLayer (pydeck)

**1. เตรียม GeoJSON**

- โหลด Thailand province boundaries GeoJSON (หาได้จาก GADM หรือ OpenStreetMap)
- บันทึกเป็น `data/thailand_provinces.geojson`
- สำหรับ district level: `data/thailand_districts.geojson`

**2. แก้ไข `map_view.py`**

เปลี่ยนจาก `ScatterplotLayer` เป็น `GeoJsonLayer`:

```python
import pydeck as pdk
import json

def render_map(data: list[dict], geojson_path: str = "data/thailand_provinces.geojson"):
    # สร้าง dict ของ rain_level ต่อจังหวัด
    level_map = {d["province"]: d["rain_level"] for d in data}
    prob_map  = {d["province"]: d["rain_probability"] for d in data}

    # โหลด GeoJSON และ inject color ตาม rain_level
    with open(geojson_path, encoding="utf-8") as f:
        geojson = json.load(f)

    for feature in geojson["features"]:
        prov = feature["properties"].get("NAME_1")   # ชื่อ field ขึ้นกับ GeoJSON source
        level = level_map.get(prov, "No Rain")
        feature["properties"]["fill_color"] = RAIN_COLORS.get(level, [150, 150, 150, 80])
        feature["properties"]["rain_level"] = level
        feature["properties"]["rain_probability"] = prob_map.get(prov, 0)

    layer = pdk.Layer(
        "GeoJsonLayer",
        data=geojson,
        get_fill_color="properties.fill_color",
        get_line_color=[255, 255, 255, 40],
        line_width_min_pixels=1,
        pickable=True,
        opacity=0.75,
        stroked=True,
    )
    ...
```

**3. ปรับ RAIN_COLORS** ให้ alpha สูงขึ้นเล็กน้อย (แนะนำ 160–200) เพราะ choropleth ต้องการสีชัดกว่า dot

**4. Tooltip** ปรับให้ใช้ `properties.NAME_1` (หรือชื่อฟิลด์ใน GeoJSON) แทน column `province`

**Note**: ตรวจสอบว่าชื่อจังหวัดใน GeoJSON ตรงกับชื่อใน `data/provinces.json` — อาจต้องทำ name mapping table ถ้าใช้ทับศัพท์ต่างกัน

---

### [FEAT-03] แสดงทุกจังหวัดใน 3-Day Forecast (All Provinces Visible by Default)

**Business requirement**: Section "3-Day Forecast by Region" ต้องแสดงทุกจังหวัดโดยไม่ต้องคลิก expand ทีละภาค

**ไฟล์ที่ต้องแก้**: `app/main.py` (บริเวณ 3-Day Forecast Accordion section)

#### แนวทางที่แนะนำ: Flat Table แทน Expander

เปลี่ยน layout จาก expander-per-region เป็นตาราง/grid แสดงครบทุกจังหวัด:

```python
# แทนที่ expander loop ด้วย flat display
for region in regions_in_data:
    region_data = [d for d in data if d.get("region") == region]
    dot_color = REGION_DOT_COLORS.get(region, "#888780")

    # Region header — ไม่ใช้ expander แต่ใช้ markdown subheader
    st.markdown(
        f'<div style="display:flex; align-items:center; gap:8px; margin: 16px 0 8px 0;">'
        f'<span style="width:8px;height:8px;border-radius:50%;background:{dot_color};display:inline-block;"></span>'
        f'<span style="font-size:14px; font-weight:500; color:var(--color-text-primary);">{region}</span>'
        f'<span style="font-size:12px; color:var(--color-text-tertiary);">({len(region_data)} จังหวัด)</span>'
        f'</div>',
        unsafe_allow_html=True
    )

    # แสดงทุกจังหวัดใน region โดยไม่ต้อง expand
    for doc in region_data:
        # ... forecast card เหมือนเดิม แต่ไม่ wrap ใน st.expander
```

#### Option เสริม: st.dataframe แบบ flat

ถ้า business ต้องการ compact มากขึ้น สามารถแสดงเป็น DataFrame เดียวที่มีคอลัมน์:
`Province | Region | Today | D+1 | D+2 | D+3` — ครบทุกจังหวัดในหน้าเดียว

#### สิ่งที่ต้องระวัง

- ถ้า filter ไม่ได้เลือก rain level ใดเป็นพิเศษ อาจแสดง 77 จังหวัดพร้อมกัน — ควรเพิ่ม `st.container(height=600)` หรือ virtual scroll
- ลบ `expanded=(region == regions_in_data[0])` ออกไป เพราะไม่ใช้ expander อีกต่อไป
- ตรวจสอบ performance — การ render 77 × 3 forecast cards พร้อมกันอาจช้า พิจารณาใช้ DataFrame แทน individual markdown cards

---

## Design System Reference

Project ใช้ design tokens ดังนี้ (กำหนดใน `app/main.py` CSS block):

| Token | Value | ใช้กับ |
|---|---|---|
| `--color-bg-primary` | `#0f1011` | Sidebar, cards |
| `--color-bg-secondary` | `#191a1b` | Hover states |
| `--color-text-primary` | `#f7f8f8` | Headings |
| `--color-text-tertiary` | `#8a8f98` | Labels, captions |
| `--color-accent-blue` | `#5e6ad2` | Interactive elements |
| `--color-teal` | `#10b981` | Moderate rain |
| `--color-amber` | `#E89558` | Heavy rain |
| `--color-red` | `#EA2143` | Very heavy rain |

### Rain Color Mapping (pydeck RGBA)

```python
RAIN_COLORS = {
    "No Rain":         [150, 150, 150, 140],
    "Light Rain":      [29, 158, 117, 160],
    "Moderate Rain":   [29, 158, 117, 200],
    "Heavy Rain":      [239, 159, 39, 220],
    "Very Heavy Rain": [226, 75, 74, 240],
}
```

---

## Region Color Reference

```python
REGION_DOT_COLORS = {
    "Central":      "#378ADD",
    "Northern":     "#E24B4A",
    "Northeastern": "#EF9F27",
    "Eastern":      "#1D9E75",
    "Southern":     "#7F77DD",
    "Western":      "#888780",
}
```

---

## ETL & Cron Reference

```bash
# รัน ETL ด้วยตนเอง
python etl/fetch_weather.py                    # morning round (default)
python etl/fetch_weather.py --round afternoon  # afternoon round

# Cron schedule (UTC)
0 22 * * *  python etl/fetch_weather.py --round morning    # 05:00 Bangkok
0  6 * * *  python etl/fetch_weather.py --round afternoon  # 13:00 Bangkok
```

Secrets ต้องตั้งค่าใน `.streamlit/secrets.toml`:

```toml
[mongodb]
uri        = "mongodb+srv://..."
db_name    = "weather_db"
collection = "forecasts"
```

หรือผ่าน environment variables สำหรับ CI/CD: `MONGODB_URI`, `MONGODB_DB_NAME`, `MONGODB_COLLECTION`

---

## Known Constraints

- **Open-Meteo free tier**: max 600 calls/min, ไม่ต้องใช้ API key — ปลอดภัยสำหรับ 77 จังหวัดหรือ ~928 อำเภอ
- **pydeck + Streamlit**: `GeoJsonLayer` รองรับ polygon fill ได้ดี แต่ต้องโหลด GeoJSON file ทั้งหมดลง memory — ควร cache ด้วย `@st.cache_data`
- **MongoDB upsert key**: `(date, province)` — ถ้าเพิ่ม district level ต้องใช้ key ใหม่ `(date, district, level)` เพื่อไม่ชนกัน
- **pandas compatibility**: `table_view.py` ใช้ `.map()` แทน `.applymap()` เพื่อรองรับ pandas ≥ 2.1 — อย่า revert กลับ

---

## Testing Checklist (ก่อน deploy)

- [ ] FEAT-01: ETL รัน `--level district` แล้ว upsert ข้อมูลได้ครบโดยไม่ error
- [ ] FEAT-01: Sidebar toggle Province/District ทำงานถูกต้อง, filter region ยังใช้งานได้
- [ ] FEAT-02: Choropleth map ระบายสีครบทุกจังหวัดที่มีข้อมูล, hover tooltip แสดงถูกต้อง
- [ ] FEAT-02: จังหวัดที่ถูก filter ออกไป (rain level filter) แสดงเป็น gray หรือ hidden ตาม design decision
- [ ] FEAT-03: 3-Day Forecast section แสดงครบทุกจังหวัดใน region โดยไม่ต้อง expand
- [ ] FEAT-03: Performance ยังรับได้เมื่อแสดง 77 จังหวัดพร้อมกัน
- [ ] Export CSV/Excel ยังทำงานถูกต้องหลังเพิ่ม district field
