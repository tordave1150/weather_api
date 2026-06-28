# agents.md — Weather Advisor Upgrade Spec

> **Repo:** `tordave1150/weather_api`  
> **Stack:** Streamlit · Python · MongoDB Atlas · Open-Meteo API · PyDeck  
> **Purpose:** คู่มือนี้เป็น instruction set สำหรับ AI agent ในการ implement 3 tasks ต่อไปนี้ทีละขั้นตอน โดยต้องไม่ทำลาย logic หรือ ETL pipeline ที่มีอยู่

---

## Project Understanding

```
weather_api/
├── app/
│   ├── main.py                  # entry point — st.set_page_config + layout
│   ├── db.py                    # MongoDB connection & queries
│   ├── weather.py               # Open-Meteo API client + rain_level logic
│   └── components/
│       ├── sidebar.py           # date / region / rain level / province filters
│       ├── map_view.py          # pydeck ScatterplotLayer map
│       ├── table_view.py        # province forecast data table
│       └── export.py            # CSV / JSON export buttons
├── etl/
│   └── fetch_weather.py         # cron ETL: Open-Meteo → MongoDB upsert
├── data/
│   └── provinces.json           # lat/lon ของ 77 จังหวัด
└── requirements.txt
```

### Data model (MongoDB document)

```json
{
  "date": "2026-06-21",
  "province": "Bangkok",
  "region": "Central",
  "rain_probability": 81,
  "rain_level": "Very Heavy Rain",
  "precipitation_sum": 12.4,
  "day_plus_1_prob": 45,
  "day_plus_2_prob": 72,
  "day_plus_3_prob": 88,
  "fetch_round": "afternoon",
  "logged_at": "2026-06-21T13:00:00+07:00"
}
```

### Rain level classification (อย่าแก้ logic นี้)

| rain_probability | rain_level        |
|-----------------|-------------------|
| < 20%           | No Rain           |
| 20–39%          | Light Rain        |
| 40–59%          | Moderate Rain     |
| 60–79%          | Heavy Rain        |
| ≥ 80%           | Very Heavy Rain   |

---

## Task 1 — 3D Hero Section (Particle Animation)

### เป้าหมาย

เพิ่ม 3D animated hero section ที่ inject ผ่าน `st.markdown(..., unsafe_allow_html=True)` ใน `app/main.py` ก่อน KPI cards — ให้ทำงานได้ใน Streamlit Cloud / GitHub โดยไม่ต้องใช้ Three.js หรือ WebGL library ภายนอก (ใช้ Canvas API 2D แทนเพราะ Streamlit iframe sandbox บล็อก WebGL ในบางกรณี)

### การวิเคราะห์ constraint ของ Streamlit

```
Streamlit renders HTML via st.markdown() inside a sandboxed iframe.
Constraints:
  - ✅ Canvas 2D API — ใช้ได้ปกติ
  - ✅ requestAnimationFrame — ใช้ได้
  - ✅ Inline <script> inside st.markdown — ใช้ได้
  - ⚠️  Three.js / WebGL — อาจถูก block ใน Streamlit Cloud
  - ❌ External JS CDN อาจช้าหรือถูก CSP block
  - ❌ position: fixed — ทำงานไม่ถูกต้องใน Streamlit iframe
```

### วิธี implement ที่ถูกต้อง

**สร้างไฟล์ใหม่:** `app/components/hero_3d.py`

```python
def render_hero_3d(rain_prob_avg: float, high_rain_count: int, date_str: str) -> str:
    """
    Returns HTML string containing a Canvas-based 3D particle sphere hero.
    rain_prob_avg  : float  — ใช้ปรับสีและความหนาแน่นของ particles (สูง = แดง/ม่วง, ต่ำ = ฟ้า/เขียว)
    high_rain_count: int    — ใช้แสดง KPI บน hero
    date_str       : str    — วันที่ที่เลือกใน sidebar
    """
    # คำนวณสี particle ตาม rain_prob_avg
    # 0–39%   → particle สีฟ้า (rgba 96,165,250)
    # 40–69%  → particle สีม่วง (rgba 167,139,250) + teal
    # 70–100% → particle สีแดง (rgba 239,68,68) + ส้ม

    if rain_prob_avg < 40:
        color_a = "96,165,250"   # blue
        color_b = "45,212,191"   # teal
        mood   = "Low risk"
    elif rain_prob_avg < 70:
        color_a = "167,139,250"  # purple
        color_b = "251,191,36"   # amber
        mood   = "Moderate risk"
    else:
        color_a = "239,68,68"    # red
        color_b = "251,146,60"   # orange
        mood   = "High risk"

    return f"""
    <div id="wa-hero" style="
        position:relative;
        height:280px;
        background:linear-gradient(135deg,#0a0f1a 0%,#0d1b2e 100%);
        border-radius:16px;
        overflow:hidden;
        margin-bottom:16px;
    ">
      <canvas id="wa-canvas" style="position:absolute;inset:0;width:100%;height:100%"></canvas>
      
      <!-- left text overlay -->
      <div style="position:absolute;left:28px;top:50%;transform:translateY(-50%);z-index:5;pointer-events:none">
        <div style="font-size:10px;font-weight:600;letter-spacing:2px;text-transform:uppercase;
                    color:#60A5FA;margin-bottom:8px">
          Live · {date_str}
        </div>
        <div style="font-size:26px;font-weight:500;color:#F9FAFB;line-height:1.2;max-width:220px">
          Thailand<br>Weather<br>Forecast
        </div>
        <div style="display:inline-flex;align-items:center;gap:6px;
                    background:rgba(239,68,68,0.15);border:0.5px solid rgba(239,68,68,0.3);
                    border-radius:20px;padding:4px 12px;font-size:11px;color:#FCA5A5;margin-top:12px">
          ⚠ {high_rain_count} high-rain provinces · Avg {rain_prob_avg:.0f}% prob
        </div>
      </div>

      <!-- mood badge top-right -->
      <div style="position:absolute;top:16px;right:16px;z-index:5;
                  background:rgba(255,255,255,0.07);border:0.5px solid rgba(255,255,255,0.12);
                  border-radius:8px;padding:6px 12px;font-size:11px;color:rgba(255,255,255,0.7)">
        {mood}
      </div>
    </div>

    <script>
    (function(){{
      const canvas = document.getElementById('wa-canvas');
      const hero   = document.getElementById('wa-hero');
      if(!canvas || !hero) return;
      const ctx = canvas.getContext('2d');
      const CA  = '{color_a}';
      const CB  = '{color_b}';
      const N   = 280;

      function resize(){{
        canvas.width  = hero.offsetWidth  || 800;
        canvas.height = hero.offsetHeight || 280;
      }}
      resize();

      const W = () => canvas.width;
      const H = () => canvas.height;
      const CX = () => W() * 0.72;
      const CY = () => H() * 0.5;

      // build fibonacci sphere
      const particles = [];
      for(let i = 0; i < N; i++){{
        const phi   = Math.acos(1 - 2*(i+0.5)/N);
        const theta = Math.PI*(1+Math.sqrt(5))*i;
        const r = 95;
        particles.push({{
          ox: Math.sin(phi)*Math.cos(theta)*r,
          oy: Math.sin(phi)*Math.sin(theta)*r,
          oz: Math.cos(phi)*r,
          trail: [],
          size : 1.2 + Math.random()*1.6,
          phase: Math.random()*Math.PI*2,
          color: Math.random() > 0.5 ? CA : CB
        }});
      }}

      let t = 0;
      let mx = CX(), my = CY();
      hero.addEventListener('mousemove', e => {{
        const r = canvas.getBoundingClientRect();
        mx = e.clientX - r.left;
        my = e.clientY - r.top;
      }});

      function frame(){{
        ctx.clearRect(0,0,W(),H());
        t += 0.007;

        const tiltX = (my - CY()) * 0.0014;
        const tiltY = (mx - CX()) * 0.001 + t*0.45;
        const cX=Math.cos(tiltX),sX=Math.sin(tiltX);
        const cY=Math.cos(tiltY),sY=Math.sin(tiltY);
        const fov=300;

        const proj = particles.map(p => {{
          const b = 1 + 0.05*Math.sin(t*1.1 + p.phase);
          const bx=p.ox*b, by=p.oy*b, bz=p.oz*b;
          const x1= bx*cY + bz*sY;
          const z1=-bx*sY + bz*cY;
          const y2= by*cX - z1*sX;
          const z2= by*sX + z1*cX;
          const dz = fov+z2;
          const px = CX() + x1*fov/dz;
          const py = CY() + y2*fov/dz;
          const sc = fov/dz;

          // mouse repulsion
          const dx=px-mx, dy=py-my, d2=dx*dx+dy*dy;
          let rpx=px, rpy=py;
          if(d2<2500){{ const d=Math.sqrt(d2)||1; const f=(50-d)*0.2; rpx+=dx/d*f; rpy+=dy/d*f; }}

          p.trail.push({{x:rpx,y:rpy}});
          if(p.trail.length>7) p.trail.shift();
          return {{p,rpx,rpy,sc,z2}};
        }});

        proj.sort((a,b)=>a.z2-b.z2);

        proj.forEach(({{{p,rpx,rpy,sc}}})=>{{
          const alpha = 0.15 + sc*0.65;
          const sz    = p.size * sc * 1.3;

          if(p.trail.length>2){{
            ctx.beginPath();
            ctx.moveTo(p.trail[0].x, p.trail[0].y);
            for(let k=1;k<p.trail.length;k++) ctx.lineTo(p.trail[k].x,p.trail[k].y);
            ctx.strokeStyle=`rgba(${{p.color}},${{alpha*0.2}})`;
            ctx.lineWidth=sz*0.4;
            ctx.lineCap='round';
            ctx.stroke();
          }}

          ctx.beginPath();
          ctx.arc(rpx,rpy,Math.max(sz*0.5,0.5),0,Math.PI*2);
          ctx.fillStyle=`rgba(${{p.color}},${{alpha}})`;
          ctx.fill();
        }});

        requestAnimationFrame(frame);
      }}
      frame();
      window.addEventListener('resize', resize);
    }})();
    </script>
    """
```

### Integrate เข้า main.py

เพิ่มใน `app/main.py` หลัง load data และก่อน KPI columns:

```python
from app.components.hero_3d import render_hero_3d

# หลัง load data จาก MongoDB...
rain_prob_avg   = filtered_df["rain_probability"].mean() if not filtered_df.empty else 0
high_rain_count = len(filtered_df[filtered_df["rain_probability"] >= 40])

st.markdown(
    render_hero_3d(
        rain_prob_avg   = round(rain_prob_avg, 1),
        high_rain_count = high_rain_count,
        date_str        = str(selected_date),
    ),
    unsafe_allow_html=True,
)
```

### Integrate กับทุก pages (ถ้า multipage)

ถ้า project เพิ่ม Streamlit multipage ในอนาคต (`pages/` folder):

```python
# pages/overview.py, pages/map.py, pages/table.py ทุกไฟล์ ให้ import hero_3d เหมือนกัน
# แต่ปรับ parameter ตาม context ของ page นั้นๆ
# เช่น pages/map.py อาจใช้ rain_prob เฉพาะภาคที่กรองอยู่
```

---

## Task 2 — Theme Redesign (Light + Weather-Aware)

### ปัญหาปัจจุบัน

Dashboard theme มืดเกินไป (`#111827` / `#1F2937` backgrounds) ทำให้ตารางข้อมูลและ map labels อ่านยาก โดยเฉพาะบน projector หรือหน้าจอกลางแจ้ง

### Design System ใหม่ — "Sky Palette"

```python
# app/theme.py  (สร้างไฟล์ใหม่)

THEME = {
    # Base surfaces
    "bg_page"     : "#F0F7FF",   # ฟ้าอ่อนมาก — เหมือนท้องฟ้าตอนเช้า
    "bg_card"     : "#FFFFFF",
    "bg_sidebar"  : "#EBF4FF",
    "bg_header"   : "linear-gradient(135deg, #1D4ED8 0%, #2563EB 50%, #3B82F6 100%)",

    # Text
    "text_primary"  : "#0F172A",  # เกือบดำ อ่านง่ายบนขาว
    "text_secondary": "#475569",
    "text_muted"    : "#94A3B8",
    "text_on_hero"  : "#FFFFFF",

    # Rain level colors (อย่าเปลี่ยน logic — เปลี่ยนแค่สีที่แสดง)
    "no_rain"      : {"bg": "#F0FDF4", "text": "#166534", "border": "#86EFAC"},
    "light_rain"   : {"bg": "#ECFDF5", "text": "#065F46", "border": "#6EE7B7"},
    "moderate_rain": {"bg": "#FFF7ED", "text": "#9A3412", "border": "#FED7AA"},
    "heavy_rain"   : {"bg": "#FFF1F2", "text": "#881337", "border": "#FECDD3"},
    "very_heavy"   : {"bg": "#EDE9FE", "text": "#4C1D95", "border": "#C4B5FD"},

    # Map dot colors (สอดคล้องกับ README color guide)
    "map_green"    : [34, 197, 94],    # < 40%
    "map_yellow"   : [250, 204, 21],   # 40–59%
    "map_orange"   : [249, 115, 22],   # 60–79%
    "map_red"      : [239, 68, 68],    # ≥ 80%
}
```

### CSS injection สำหรับ Streamlit

สร้างฟังก์ชัน `apply_theme()` ใน `app/theme.py`:

```python
def apply_theme() -> None:
    """Inject global CSS. เรียกครั้งเดียวใน main.py ก่อน render อื่นๆ"""
    import streamlit as st
    st.markdown("""
    <style>
    /* ── Page background ── */
    .stApp { background: #F0F7FF !important; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #EBF4FF !important;
        border-right: 1px solid #BFDBFE !important;
    }
    [data-testid="stSidebar"] * { color: #0F172A !important; }
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
        background: #DBEAFE !important;
        color: #1E40AF !important;
    }

    /* ── KPI metric cards ── */
    [data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1px solid #BFDBFE !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        box-shadow: 0 1px 6px rgba(37,99,235,0.08) !important;
    }
    [data-testid="stMetricLabel"] { color: #64748B !important; font-size: 12px !important; }
    [data-testid="stMetricValue"] { color: #0F172A !important; font-size: 1.8rem !important; }

    /* ── Data table ── */
    [data-testid="stDataFrame"] { background: #FFFFFF !important; }
    [data-testid="stDataFrame"] table { color: #0F172A !important; }
    [data-testid="stDataFrame"] thead th {
        background: #EFF6FF !important;
        color: #1E40AF !important;
        font-weight: 600 !important;
        font-size: 11px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    [data-testid="stDataFrame"] tbody tr:nth-child(odd) { background: #F8FAFF !important; }
    [data-testid="stDataFrame"] tbody tr:hover { background: #DBEAFE !important; }

    /* ── Expander (3-day accordion) ── */
    [data-testid="stExpander"] {
        background: #FFFFFF !important;
        border: 1px solid #BFDBFE !important;
        border-radius: 10px !important;
        margin-bottom: 6px !important;
    }
    [data-testid="stExpander"] summary { color: #1E40AF !important; font-weight: 500 !important; }

    /* ── Buttons ── */
    .stButton > button {
        background: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
    }
    .stButton > button:hover { background: #1D4ED8 !important; }

    /* ── Download buttons ── */
    .stDownloadButton > button {
        background: #FFFFFF !important;
        color: #2563EB !important;
        border: 1px solid #93C5FD !important;
        border-radius: 8px !important;
    }

    /* ── Section headers ── */
    h1, h2, h3 { color: #0F172A !important; }
    h1 { font-size: 1.4rem !important; }
    h2 { font-size: 1.1rem !important; border-bottom: 1px solid #BFDBFE; padding-bottom: 6px; }

    /* ── Alert / info boxes ── */
    [data-testid="stAlert"] {
        background: #FFF7ED !important;
        border-left: 4px solid #F97316 !important;
        color: #7C2D12 !important;
        border-radius: 0 8px 8px 0 !important;
    }

    /* ── Selectbox / DateInput ── */
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stDateInput"] > div > div {
        background: #FFFFFF !important;
        border: 1px solid #93C5FD !important;
        border-radius: 8px !important;
        color: #0F172A !important;
    }

    /* ── Map container ── */
    iframe { border-radius: 12px !important; }

    /* ── Global font ── */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)
```

### Weather-aware dynamic theming

ระบบควรเปลี่ยน theme ตาม avg rain probability ที่ filter อยู่:

```python
# app/theme.py

def get_hero_gradient(rain_prob_avg: float) -> str:
    """Returns CSS gradient string based on current weather severity."""
    if rain_prob_avg < 40:
        # Clear / light — sky blue to cyan
        return "linear-gradient(135deg, #0EA5E9 0%, #38BDF8 50%, #7DD3FC 100%)"
    elif rain_prob_avg < 70:
        # Moderate — blue-grey to slate
        return "linear-gradient(135deg, #1E40AF 0%, #2563EB 50%, #6366F1 100%)"
    else:
        # Heavy / very heavy — deep blue to purple (stormy)
        return "linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4C1D95 100%)"


def get_alert_level(very_heavy_count: int) -> dict:
    """Returns alert config. Alert bar แสดงเมื่อ very_heavy_count >= 10 (ตาม README spec)."""
    if very_heavy_count >= 20:
        return {"show": True, "level": "critical", "color": "#7F1D1D",
                "bg": "#FEE2E2", "icon": "🔴",
                "msg": f"Critical: {very_heavy_count} provinces with Very Heavy Rain"}
    elif very_heavy_count >= 10:
        return {"show": True, "level": "warning", "color": "#7C2D12",
                "bg": "#FFF7ED", "icon": "⚠️",
                "msg": f"Warning: {very_heavy_count} provinces with Very Heavy Rain"}
    else:
        return {"show": False}
```

### ปรับ map_view.py ให้ใช้สีใหม่

```python
# app/components/map_view.py
# แก้ color logic ใน ScatterplotLayer:

def get_dot_color(rain_prob: int) -> list:
    """Map rain_probability to RGBA list for pydeck."""
    if rain_prob < 40:
        return [34, 197, 94, 200]    # green
    elif rain_prob < 60:
        return [250, 204, 21, 200]   # yellow
    elif rain_prob < 80:
        return [249, 115, 22, 210]   # orange
    else:
        return [239, 68, 68, 220]    # red

# ใน render_map():
df["color"] = df["rain_probability"].apply(get_dot_color)

layer = pdk.Layer(
    "ScatterplotLayer",
    data=df,
    get_position=["lon", "lat"],
    get_color="color",
    get_radius=30000,
    pickable=True,
    auto_highlight=True,
)

# ใช้ light map style แทน dark
deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/light-v10",  # เปลี่ยนจาก dark-v10
    tooltip={
        "html": "<b>{province}</b><br>Rain: {rain_probability}%<br>Level: {rain_level}",
        "style": {
            "backgroundColor": "white",
            "color": "#0F172A",
            "borderRadius": "8px",
            "padding": "8px 12px",
            "fontSize": "13px",
            "border": "1px solid #BFDBFE",
        }
    }
)
```

### เรียก apply_theme() ใน main.py

```python
# app/main.py — บรรทัดแรกหลัง st.set_page_config()

from app.theme import apply_theme, get_hero_gradient, get_alert_level
apply_theme()
```

---

## Task 3 — Caching (แก้ปัญหา map โหลดช้า)

### ปัญหาปัจจุบัน

ทุกครั้งที่ user refresh หรือเปลี่ยน filter Streamlit จะ re-query MongoDB และ re-render map ใหม่ทั้งหมด ทำให้รอนาน

### Strategy

ใช้ **3 layers** ของ cache ตาม Streamlit caching system:

| Layer | Scope | TTL | ใช้สำหรับ |
|-------|-------|-----|-----------|
| `@st.cache_resource` | global (ข้าม session) | ไม่หมดอายุ | MongoDB connection object |
| `@st.cache_data` | per-argument hash | 10 นาที | ผลลัพธ์ query จาก DB |
| `@st.cache_data` | per-argument hash | 60 นาที | pydeck Deck object (heavy) |

### Implementation

#### 3a — Cache MongoDB connection (`app/db.py`)

```python
import streamlit as st
from pymongo import MongoClient

@st.cache_resource   # สร้าง connection ครั้งเดียว ใช้ข้าม session
def get_mongo_client() -> MongoClient:
    """Return a shared MongoClient. Streamlit reuses this across all reruns."""
    uri = st.secrets["mongodb"]["uri"]
    return MongoClient(uri, serverSelectionTimeoutMS=5000)


@st.cache_data(ttl=600)   # cache 10 นาที — ข้อมูล refresh ทุก 10 นาทีพอ
def fetch_weather_data(date_str: str, regions: tuple, rain_levels: tuple) -> list[dict]:
    """
    Query MongoDB with filter parameters.
    ใช้ tuple แทน list เพราะ st.cache_data hash ต้องการ hashable types.

    Args:
        date_str   : "2026-06-21"
        regions    : ("Central", "Northern") — tuple เสมอ
        rain_levels: ("Heavy Rain", "Very Heavy Rain") — tuple เสมอ

    Returns:
        list of dicts (MongoDB documents)
    """
    client = get_mongo_client()
    db     = client[st.secrets["mongodb"]["db_name"]]
    col    = db[st.secrets["mongodb"]["collection"]]

    query: dict = {"date": date_str}

    if regions:
        query["region"] = {"$in": list(regions)}
    if rain_levels:
        query["rain_level"] = {"$in": list(rain_levels)}

    docs = list(col.find(query, {"_id": 0}))
    return docs
```

#### 3b — Cache pydeck map object (`app/components/map_view.py`)

```python
import streamlit as st
import pydeck as pdk
import pandas as pd

@st.cache_data(ttl=3600, show_spinner="Preparing map…")
def build_pydeck(date_str: str, regions: tuple, rain_levels: tuple) -> pdk.Deck:
    """
    Build and cache the full pydeck.Deck object.
    TTL = 1 ชั่วโมง เพราะ map geometry ไม่เปลี่ยนบ่อย

    Note: pydeck Deck is serializable by st.cache_data.
    """
    from app.db import fetch_weather_data
    docs = fetch_weather_data(date_str, regions, rain_levels)
    df   = pd.DataFrame(docs)

    if df.empty:
        return _empty_deck()

    # load province coordinates
    import json, os
    coord_path = os.path.join(os.path.dirname(__file__), "../../data/provinces.json")
    with open(coord_path) as f:
        coords = {p["province"]: p for p in json.load(f)}

    df["lat"] = df["province"].map(lambda p: coords.get(p, {}).get("lat"))
    df["lon"] = df["province"].map(lambda p: coords.get(p, {}).get("lon"))
    df        = df.dropna(subset=["lat", "lon"])

    df["color"] = df["rain_probability"].apply(_get_dot_color)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius=28000,
        pickable=True,
        auto_highlight=True,
    )

    view = pdk.ViewState(latitude=13.0, longitude=101.5, zoom=5.0, pitch=0)

    return pdk.Deck(
        layers=[layer],
        initial_view_state=view,
        map_style="mapbox://styles/mapbox/light-v10",
        tooltip={
            "html": "<b>{province}</b><br>Rain prob: {rain_probability}%<br>{rain_level}",
            "style": {"backgroundColor": "white", "color": "#0F172A",
                      "borderRadius": "8px", "padding": "8px 12px", "fontSize": "13px"}
        }
    )


def _get_dot_color(prob: int) -> list:
    if prob < 40:  return [34, 197, 94, 200]
    if prob < 60:  return [250, 204, 21, 200]
    if prob < 80:  return [249, 115, 22, 210]
    return             [239, 68, 68, 220]


def _empty_deck() -> pdk.Deck:
    return pdk.Deck(
        layers=[],
        initial_view_state=pdk.ViewState(latitude=13.0, longitude=101.5, zoom=5.0),
        map_style="mapbox://styles/mapbox/light-v10",
    )


def render_map(date_str: str, regions: tuple, rain_levels: tuple) -> None:
    """Call this from main.py instead of building the deck inline."""
    deck = build_pydeck(date_str, regions, rain_levels)
    st.pydeck_chart(deck, use_container_width=True, height=460)
```

#### 3c — Cache table data (`app/components/table_view.py`)

```python
import streamlit as st
import pandas as pd

@st.cache_data(ttl=600)
def build_table_df(date_str: str, regions: tuple, rain_levels: tuple,
                   province_search: str) -> pd.DataFrame:
    """
    Build the province table DataFrame with caching.
    province_search เป็น str เพื่อ cache ได้ถูกต้อง
    """
    from app.db import fetch_weather_data
    docs = fetch_weather_data(date_str, regions, rain_levels)
    df   = pd.DataFrame(docs)

    if df.empty:
        return df

    if province_search:
        df = df[df["province"].str.contains(province_search, case=False, na=False)]

    df = df.sort_values("rain_probability", ascending=False).reset_index(drop=True)

    # rename columns for display
    df = df.rename(columns={
        "province"        : "Province",
        "region"          : "Region",
        "rain_probability": "Prob %",
        "rain_level"      : "Rain Level",
        "precipitation_sum": "Vol (mm)",
        "day_plus_1_prob" : "D+1",
        "day_plus_2_prob" : "D+2",
        "day_plus_3_prob" : "D+3",
    })

    return df[["Province", "Region", "Prob %", "Rain Level", "Vol (mm)", "D+1", "D+2", "D+3"]]
```

#### 3d — ปรับ sidebar.py ให้ส่ง tuple ไม่ใช่ list

```python
# app/components/sidebar.py
# แก้ return type ของ region และ rain_level เป็น tuple

def render_sidebar() -> dict:
    ...
    return {
        "date"          : selected_date,
        "regions"       : tuple(selected_regions),      # list → tuple
        "rain_levels"   : tuple(selected_rain_levels),  # list → tuple
        "province_search": province_search.strip(),
    }
```

#### 3e — ปรับ main.py ให้ใช้ cached functions

```python
# app/main.py

from app.components.sidebar    import render_sidebar
from app.components.map_view   import render_map
from app.components.table_view import build_table_df
from app.db                    import fetch_weather_data

filters = render_sidebar()

date_str  = str(filters["date"])
regions   = filters["regions"]        # tuple
rain_levs = filters["rain_levels"]    # tuple
prov_srch = filters["province_search"]

# fetch (cached 10 min)
docs = fetch_weather_data(date_str, regions, rain_levs)
df   = pd.DataFrame(docs)

# KPI
rain_prob_avg    = df["rain_probability"].mean() if not df.empty else 0
high_rain_count  = len(df[df["rain_probability"] >= 40])
very_heavy_count = len(df[df["rain_level"] == "Very Heavy Rain"])

# hero 3D (Task 1)
st.markdown(render_hero_3d(rain_prob_avg, high_rain_count, date_str), unsafe_allow_html=True)

# KPI cards
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Total provinces",     len(df))
with col2: st.metric("High rain zones",     high_rain_count)
with col3: st.metric("Very heavy rain",     very_heavy_count)
with col4: st.metric("Avg rain prob.",      f"{rain_prob_avg:.1f}%")

# Map (cached 60 min)
st.subheader("Province rain map")
render_map(date_str, regions, rain_levs)

# Table (cached 10 min)
st.subheader("Province forecast data")
table_df = build_table_df(date_str, regions, rain_levs, prov_srch)
st.dataframe(table_df, use_container_width=True, height=400)
```

### Local disk cache สำหรับ province coordinates

ไฟล์ `data/provinces.json` ถูกอ่านทุก render — ควร cache ไว้:

```python
# app/db.py หรือ app/utils.py

import json, os, streamlit as st

@st.cache_data   # cache ตลอด session ไม่มี TTL
def load_province_coords() -> dict:
    """Load provinces.json once per session. Returns dict keyed by province name."""
    path = os.path.join(os.path.dirname(__file__), "../data/provinces.json")
    with open(path) as f:
        data = json.load(f)
    return {p["province"]: p for p in data}
```

---

## Checklist สำหรับ AI Agent

### Task 1 — 3D Hero

- [ ] สร้าง `app/components/hero_3d.py` พร้อมฟังก์ชัน `render_hero_3d()`
- [ ] Canvas 2D ต้องใช้ `requestAnimationFrame` ไม่ใช่ `setInterval`
- [ ] Particle sphere ใช้ fibonacci distribution (ไม่ใช่ random)
- [ ] สีเปลี่ยนตาม `rain_prob_avg` (ฟ้า/เขียว → ม่วง → แดง)
- [ ] ต้องมี mouse repulsion effect
- [ ] ไม่ใช้ JS library ภายนอก (no Three.js, no CDN)
- [ ] เรียก `st.markdown(..., unsafe_allow_html=True)` ใน `main.py`

### Task 2 — Theme

- [ ] สร้าง `app/theme.py` พร้อม `apply_theme()`, `get_hero_gradient()`, `get_alert_level()`
- [ ] เรียก `apply_theme()` ก่อน render ทุกอย่างใน `main.py`
- [ ] Map style เปลี่ยนเป็น `mapbox://styles/mapbox/light-v10`
- [ ] Tooltip สีขาว พื้นหลังขาว ตัวอักษรดำ
- [ ] ไม่แก้ rain_level classification logic
- [ ] Alert bar แสดงเมื่อ `very_heavy_count >= 10` (ตาม README spec)

### Task 3 — Caching

- [ ] `get_mongo_client()` ใช้ `@st.cache_resource`
- [ ] `fetch_weather_data()` ใช้ `@st.cache_data(ttl=600)` รับ tuple ไม่ใช่ list
- [ ] `build_pydeck()` ใช้ `@st.cache_data(ttl=3600)`
- [ ] `build_table_df()` ใช้ `@st.cache_data(ttl=600)`
- [ ] `load_province_coords()` ใช้ `@st.cache_data` (no TTL)
- [ ] `sidebar.py` return `tuple` สำหรับ regions และ rain_levels
- [ ] ทดสอบ: เปิด dashboard → กด F5 → map ไม่ควร re-download ใหม่ (เห็น spinner น้อยลง)

---

## Testing

```bash
# รัน local
streamlit run app/main.py

# ตรวจสอบ cache stats (Streamlit built-in)
# ไปที่ ⋮ menu → Clear cache → กด F5 → สังเกต load time
# ครั้งแรก: ~3–5 วินาที (cold cache)
# ครั้งต่อไป: < 0.5 วินาที (warm cache) ← เป้าหมาย

# ถ้า cache ทำงานถูกต้อง จะเห็น "Preparing map…" spinner เฉพาะครั้งแรก
```

---

## Dependencies เพิ่มเติม (ถ้าจำเป็น)

```txt
# requirements.txt — ไม่ต้องเพิ่ม package ใหม่
# Task 1: ใช้ Canvas API (browser built-in)
# Task 2: ใช้ st.markdown CSS injection (Streamlit built-in)
# Task 3: ใช้ @st.cache_data / @st.cache_resource (Streamlit built-in)
```

---

*agents.md version 1.0 — สร้างจาก repo analysis ของ `tordave1150/weather_api` บน GitHub*
