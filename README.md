# ⛈ Weather Advisor — Thailand Provincial Weather Dashboard

**Weather Advisor** คือ Dashboard แสดงข้อมูลพยากรณ์อากาศรายวันของทุก 77 จังหวัดในประเทศไทย ออกแบบมาเพื่อให้ทีมธุรกิจสามารถติดตามสถานการณ์ฝนและความเสี่ยงด้านสภาพอากาศได้อย่างรวดเร็ว

---

## วิธีใช้งาน Dashboard

### การเปิดใช้งาน

```bash
streamlit run app/main.py
```

เปิดเบราว์เซอร์ที่ `http://localhost:8501`

---

## โครงสร้างหน้าจอ

```
┌──────────────────────────────────────────────────────┐
│  Sidebar (ตัวกรอง)         │   Main Area              │
│  • เลือกวันที่              │   • Hero Banner + KPIs   │
│  • กรองตามภาค              │   • แผนที่ + ตารางข้อมูล  │
│  • กรองระดับฝน             │   • พยากรณ์ 3 วัน        │
│  • ค้นหาจังหวัด             │   • Export CSV/JSON      │
└──────────────────────────────────────────────────────┘
```

### Sidebar — ตัวกรองข้อมูล

| ตัวกรอง | คำอธิบาย |
|---|---|
| **Date** | เลือกวันที่ต้องการดูข้อมูล ระบบจะแสดงเฉพาะข้อมูลของวันนั้น |
| **Region** | กรองตามภาค (เหนือ / อีสาน / กลาง / ตะวันออก / ตะวันตก / ใต้) |
| **Rain Level** | กรองตามระดับความรุนแรงของฝน ค่าเริ่มต้นแสดงเฉพาะระดับ Moderate ขึ้นไป |
| **Province** | พิมพ์ค้นหาชื่อจังหวัดได้โดยตรง |

---

## แหล่งที่มาของข้อมูล

ข้อมูลทั้งหมดมาจาก **[Open-Meteo API](https://open-meteo.com/)** — บริการพยากรณ์อากาศฟรีที่ไม่ต้องใช้ API Key (Free Tier)

- **URL**: `https://api.open-meteo.com/v1/forecast`
- **ความถี่ในการดึงข้อมูล**: วันละ 2 รอบ (ผ่าน Cron → `etl/fetch_weather.py`)
  - 🌅 **Morning round** — 05:00 น. เวลาไทย (UTC 22:00)
  - 🌇 **Afternoon round** — 13:00 น. เวลาไทย (UTC 06:00)
- **พิกัดจังหวัด**: เก็บไว้ใน `data/provinces.json` ครบทั้ง 77 จังหวัด
- **ฐานข้อมูล**: MongoDB Atlas — เก็บข้อมูลพยากรณ์รายวันต่อจังหวัด

> 💡 รอบ Afternoon จะ **overwrite** ข้อมูลรอบ Morning ของวันเดียวกันอัตโนมัติ เพราะ upsert key คือ `(date, province)`

---

## ค่าแต่ละค่าในหน้า Dashboard

### 🔢 KPI Cards (ด้านบนสุด)

| ชื่อ | ที่มา | วิธีคำนวณ |
|---|---|---|
| **Total Provinces** | ข้อมูลที่ผ่านการกรองแล้ว | นับจำนวน doc ที่แสดงผลหลังกรอง Region / Rain Level / Province |
| **High Rain Zones** | `rain_probability` จาก Open-Meteo | นับจังหวัดที่มี `rain_probability ≥ 40%` |
| **Very Heavy Rain** | `rain_level` (calculated) | นับจังหวัดที่ถูก classify ว่า `"Very Heavy Rain"` |
| **Avg Rain Probability** | `rain_probability` | ค่าเฉลี่ยของ `rain_probability` ทุกจังหวัดที่แสดงอยู่ |

> ⚠️ **Alert Bar** จะปรากฏโดยอัตโนมัติเมื่อมีจังหวัดที่ระดับ Very Heavy Rain **≥ 10 จังหวัด**

---

### 🗺️ Province Rain Map (แผนที่)

แสดงจุดแต่ละจังหวัดบนแผนที่ประเทศไทย ขนาดและสีของจุดสะท้อนระดับความเสี่ยงของฝน:

| สี | ระดับ |
|---|---|
| 🟢 เขียว | ฝนน้อย (< 40%) |
| 🟡 เหลือง | ฝนปานกลาง (40–59%) |
| 🟠 ส้ม | ฝนหนัก (60–79%) |
| 🔴 แดง | ฝนหนักมาก (≥ 80%) |

---

### 📋 Province Forecast Data Table (ตาราง)

ตารางแสดงข้อมูลจังหวัด เรียงลำดับจาก `rain_probability` มากไปน้อย

| คอลัมน์ | ที่มา | คำอธิบาย |
|---|---|---|
| **Province** | `province_coords` (provinces.json) | ชื่อจังหวัด |
| **Region** | MongoDB → `region` field | ภาคที่จังหวัดสังกัด |
| **Prob %** | Open-Meteo → `precipitation_probability_max` (index 0 = today) | ความน่าจะเป็นของฝนวันนี้ (%) |
| **Rain Level** | **Calculated** (ดูตารางด้านล่าง) | ระดับความรุนแรงของฝนที่คำนวณจาก Prob % |
| **Vol (mm)** | Open-Meteo → `precipitation_sum` (index 0) | ปริมาณน้ำฝนรวมที่คาดว่าจะตกวันนี้ (mm) |
| **D+1** | Open-Meteo → `precipitation_probability_max` (index 1) | ความน่าจะเป็นฝนวันพรุ่งนี้ (%) |
| **D+2** | Open-Meteo → `precipitation_probability_max` (index 2) | ความน่าจะเป็นฝนอีก 2 วัน (%) |
| **D+3** | Open-Meteo → `precipitation_probability_max` (index 3) | ความน่าจะเป็นฝนอีก 3 วัน (%) |

---

### 🏷️ Rain Level Classification (การจัดประเภทระดับฝน)

`rain_level` เป็นค่าที่ **คำนวณโดยระบบ** (ไม่ได้มาจาก API โดยตรง) โดยใช้ `rain_probability` เป็นตัวตัดสิน:

| Prob % | Rain Level | Badge |
|---|---|---|
| < 20% | **No Rain** | ☀️ ไม่มีฝน |
| 20–39% | **Light Rain** | 🌤 ฝนเล็กน้อย |
| 40–59% | **Moderate Rain** | 🌦 ฝนปานกลาง |
| 60–79% | **Heavy Rain** | 🌧 ฝนหนัก |
| ≥ 80% | **Very Heavy Rain** | ⛈ ฝนหนักมาก |

> 💡 **ข้อสังเกต**: การจัดประเภทนี้อิงจาก *ความน่าจะเป็น* (Probability) ไม่ใช่ปริมาณน้ำฝนจริง (Volume) ดังนั้น จังหวัดที่มี Prob % = 100 อาจมีปริมาณน้ำฝน (Vol mm) น้อยได้ หาก Open-Meteo forecast บอกว่าฝนตกแน่ แต่ปริมาณน้อย

---

### 📅 3-Day Forecast by Region (พยากรณ์ 3 วัน)

ส่วนล่างสุดแสดงพยากรณ์รายจังหวัด จัดกลุ่มตามภาค เรียงจาก Rain Probability สูงสุดก่อน

| ค่าในแต่ละวัน | ที่มา |
|---|---|
| **Day+1 / Day+2 / Day+3** | Open-Meteo `precipitation_probability_max` index 1, 2, 3 |
| **ระดับฝนแต่ละวัน** | Calculated จาก Rain Level Classification ด้านบน |
| **วันที่** | Open-Meteo `time` field (YYYY-MM-DD format, Bangkok timezone) |

---

## Colour Coding Guide (ความหมายของสี)

### Probability Chips (D+1, D+2, D+3, Prob %)

| สี | ช่วงค่า | ความหมาย |
|---|---|---|
| ⬜ เทา | < 20% | โอกาสฝนน้อยมาก |
| 🟢 เขียว | 20–39% | มีโอกาสฝนเล็กน้อย |
| 🟠 ส้มอ่อน | 40–59% | ฝนปานกลาง ควรเตรียมร่ม |
| 🟠 ส้มเข้ม | 60–79% | ฝนหนัก ระวังน้ำท่วมขัง |
| 🔴 แดง | ≥ 80% | ฝนหนักมาก เสี่ยงสูง |

### Region Dots (จุดภาค)

| สี | ภาค |
|---|---|
| 🔵 น้ำเงินม่วง | ภาคกลาง (Central) |
| 🔴 แดง | ภาคเหนือ (Northern) |
| 🟠 ส้ม | ภาคตะวันออกเฉียงเหนือ (Northeastern) |
| 🟢 เขียว | ภาคตะวันออก (Eastern) |
| 🟣 ม่วง | ภาคใต้ (Southern) |
| ⬜ เทา | ภาคตะวันตก (Western) |

---

## ETL Process (วิธีอัปเดตข้อมูล)

ข้อมูลอัปเดตผ่านสคริปต์ `etl/fetch_weather.py` — รันอัตโนมัติผ่าน **GitHub Actions** วันละ 2 รอบ

### 🤖 GitHub Actions (Automated)

Workflow: `.github/workflows/etl.yml`

- ระบบจะ **รันอัตโนมัติ** วันละ 2 รอบตามตาราง Cron ด้านล่าง
- Credentials ดึงจาก **GitHub Repository Secrets** (ไม่ hardcode ในโค้ด)
- สามารถ **Manual Trigger** ได้จากแท็บ Actions บน GitHub (Run workflow)

### 🖥️ รันมือ (Local)

```bash
# ค่าเริ่มต้น = morning round
python etl/fetch_weather.py

# ระบุรอบ afternoon
python etl/fetch_weather.py --round afternoon
```

> 💡 เมื่อรันในเครื่อง สคริปต์จะอ่าน credentials จาก `.streamlit/secrets.toml` โดยอัตโนมัติ

### Cron Schedule

| รอบ | เวลาไทย (ICT) | Cron (UTC) | คำสั่ง |
|---|---|---|---|
| Morning | 05:00 น. | `0 22 * * *` | `python etl/fetch_weather.py --round morning` |
| Afternoon | 13:00 น. | `0 6 * * *` | `python etl/fetch_weather.py --round afternoon` |

### ขั้นตอน ETL
1. โหลดพิกัด 77 จังหวัดจาก `data/provinces.json`
2. เรียก Open-Meteo API ทีละจังหวัด (ห่างกัน 0.15 วินาทีเพื่อไม่เกิน rate limit)
3. คำนวณ `rain_level` จาก `rain_probability`
4. บันทึก `fetch_round` (morning/afternoon) และ `logged_at` (timestamp) ในทุก document
5. Upsert ลง MongoDB โดยใช้ `(date, province)` เป็น key — รอบ afternoon จะ overwrite รอบ morning อัตโนมัติ

---

## Tech Stack

| Layer | Technology |
|---|---|
| Dashboard | Streamlit (Python) |
| Data Source | Open-Meteo API (Free Tier, no key required) |
| Database | MongoDB Atlas |
| ETL | Python script (`etl/fetch_weather.py`) |
| CI/CD | GitHub Actions (cron schedule, 2 runs/day) |
| Design System | Linear Design System (via open-design) |
| Hosting | Streamlit Cloud / Local (`streamlit run app/main.py`) |

---

## Configuration

### Local Development

สร้างไฟล์ `.streamlit/secrets.toml`:

```toml
[mongodb]
uri        = "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/"
db_name    = "<your_database>"
collection = "<your_collection>"
```

### GitHub Actions (CI/CD)

เพิ่ม Repository Secrets ใน GitHub:

```
Settings → Secrets and variables → Actions → New repository secret
```

| Secret name | ค่า |
|---|---|
| `MONGODB_URI` | `mongodb+srv://<user>:<password>@<cluster>.mongodb.net/` |
| `MONGODB_DB_NAME` | ชื่อ database |
| `MONGODB_COLLECTION` | ชื่อ collection |

> ⚠️ **MongoDB Atlas Network Access**: ต้องอนุญาต IP `0.0.0.0/0` เพราะ GitHub Actions runners ใช้ IP ที่เปลี่ยนทุกครั้ง

---

## Project Structure

```
weather_api/
├── .github/
│   └── workflows/
│       └── etl.yml              # GitHub Actions — ETL cron (2 runs/day)
├── app/
│   ├── main.py                  # หน้าหลัก Dashboard
│   ├── db.py                    # MongoDB connection & queries
│   ├── weather.py               # Open-Meteo API client + logic
│   └── components/
│       ├── sidebar.py           # ตัวกรอง Sidebar
│       ├── map_view.py          # แผนที่จังหวัด
│       ├── table_view.py        # ตารางข้อมูลจังหวัด
│       └── export.py            # Export CSV/JSON
├── etl/
│   └── fetch_weather.py         # สคริปต์ดึงข้อมูลรายวัน (env vars + secrets.toml)
├── data/
│   └── provinces.json           # พิกัด lat/lon ของ 77 จังหวัด
└── requirements.txt
```

---

*ข้อมูลพยากรณ์อากาศเป็นการประมาณการล่วงหน้า ความแม่นยำอาจแตกต่างจากสภาพอากาศจริง โดยเฉพาะ D+2 และ D+3*
