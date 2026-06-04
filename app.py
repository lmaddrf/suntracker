import streamlit as st
import pandas as pd
from pvlib import solarposition
import requests
from datetime import datetime
import pytz

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="225 Franklin Terrace Sun Tracker",
    page_icon="☀️",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #faf9f7;
    color: #1c1c1c;
}
.block-container {
    max-width: 720px;
    padding-top: 3rem;
    padding-bottom: 3rem;
}
.header-eyebrow {
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #999;
    margin-bottom: 0.5rem;
}
.header-title {
    font-family: 'Playfair Display', serif;
    font-size: 3rem;
    font-weight: 700;
    line-height: 1.1;
    color: #1c1c1c;
    margin-bottom: 0.3rem;
}
.header-sub {
    font-size: 0.9rem;
    color: #888;
    font-weight: 400;
    margin-bottom: 2rem;
}
.sun-arc-container {
    background: linear-gradient(160deg, #fff8ed 0%, #ffefc9 100%);
    border-radius: 16px;
    padding: 2rem 2rem 1.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid #f0e4c8;
    position: relative;
    overflow: hidden;
}
.sun-arc-container::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 180px; height: 180px;
    border-radius: 50%;
    background: radial-gradient(circle, #ffde6a55 0%, transparent 70%);
}
.sun-pct-label {
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #b07d2a;
    margin-bottom: 0.5rem;
}
.sun-pct-value {
    font-family: 'Playfair Display', serif;
    font-size: 4.5rem;
    font-weight: 700;
    color: #c47d00;
    line-height: 1;
    margin-bottom: 1rem;
}
.sun-track {
    background: #f5e4b8;
    border-radius: 999px;
    height: 8px;
    width: 100%;
    overflow: hidden;
    margin-bottom: 0.5rem;
}
.sun-fill {
    height: 8px;
    border-radius: 999px;
}
.sun-meta {
    font-size: 0.78rem;
    color: #b07d2a;
    opacity: 0.8;
}
.metrics-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.metric-card {
    background: #ffffff;
    border: 1px solid #ebebeb;
    border-radius: 14px;
    padding: 1.25rem 1.1rem;
}
.metric-card-label {
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: #aaa;
    margin-bottom: 0.5rem;
}
.metric-card-value {
    font-family: 'Playfair Display', serif;
    font-size: 2.4rem;
    font-weight: 700;
    color: #1c1c1c;
    line-height: 1;
    margin-bottom: 0.3rem;
}
.metric-card-sub {
    font-size: 0.75rem;
    color: #bbb;
}
.chips-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
}
.chip {
    font-size: 0.78rem;
    color: #666;
    background: #ffffff;
    border: 1px solid #e8e8e8;
    border-radius: 999px;
    padding: 0.28rem 0.85rem;
    font-weight: 400;
}
.verdict-box {
    border-radius: 14px;
    padding: 1.3rem 1.6rem;
    font-size: 0.95rem;
    line-height: 1.6;
}
.verdict-great {
    background: linear-gradient(135deg, #edfaf3, #d6f5e6);
    border: 1px solid #a8e6c2;
    color: #1a5c3a;
}
.verdict-ok {
    background: linear-gradient(135deg, #fdfbec, #faf3d0);
    border: 1px solid #e8d87a;
    color: #6b5300;
}
.verdict-bad {
    background: linear-gradient(135deg, #fdf0f0, #fde0e0);
    border: 1px solid #f0b8b8;
    color: #7a1a1a;
}
.verdict-night {
    background: linear-gradient(135deg, #f0f0fd, #e4e4fa);
    border: 1px solid #c0c0ee;
    color: #2a2a6a;
}
.verdict-bold { font-weight: 700; }
.api-warn {
    font-size: 0.8rem;
    color: #9a6f00;
    background: #fffae8;
    border: 1px solid #f0d060;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    margin-bottom: 1.2rem;
}
</style>
""", unsafe_allow_html=True)

# ─── Constants ───────────────────────────────────────────────────────────────────
LAT, LON = 42.3556, -71.0565
BOSTON_TZ = pytz.timezone('America/New_York')

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icing fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow",
    80: "Light showers", 81: "Showers", 82: "Heavy showers",
    95: "Thunderstorm", 96: "Thunderstorm w/ hail", 99: "Thunderstorm w/ heavy hail",
}

# ─── Time & Solar ────────────────────────────────────────────────────────────────
now_boston = datetime.now(BOSTON_TZ)
solpos    = solarposition.get_solarposition(pd.Timestamp(now_boston), LAT, LON)
elevation = float(solpos['apparent_elevation'].iloc[0])
azimuth   = float(solpos['azimuth'].iloc[0])

# ─── Weather Fetch (Open-Meteo) ──────────────────────────────────────────────────
debug_info = {}
api_ok = False

weather_url = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    "&current=temperature_2m,apparent_temperature,relative_humidity_2m,"
    "cloud_cover,wind_speed_10m,wind_gusts_10m,direct_radiation,"
    "weather_code,precipitation,uv_index"
    "&temperature_unit=fahrenheit"
    "&wind_speed_unit=mph"
    "&timezone=America%2FNew_York"
)

try:
    r = requests.get(weather_url, timeout=8, verify=False)
    debug_info['http_status'] = r.status_code
    if r.status_code == 200:
        cur = r.json()['current']
        air_temp        = cur['temperature_2m']
        feels_like      = cur['apparent_temperature']
        humidity        = cur['relative_humidity_2m']
        cloud_cover     = cur['cloud_cover']
        wind_speed      = cur['wind_speed_10m']
        wind_gusts      = cur['wind_gusts_10m']
        direct_rad      = cur.get('direct_radiation', 0)
        weather_code    = cur.get('weather_code', 0)
        precipitation   = cur.get('precipitation', 0)
        uv_index        = cur.get('uv_index', None)
        condition_label = WMO_CODES.get(weather_code, "—")
        api_ok = True
        debug_info['raw'] = {k: cur[k] for k in cur}
    else:
        raise ValueError(f"HTTP {r.status_code}")
except Exception as e:
    debug_info['exception'] = str(e)
    air_temp, feels_like, humidity = 68.0, 66.0, 55
    cloud_cover, wind_speed, wind_gusts = 25, 8.0, 12.0
    direct_rad, precipitation = 350, 0
    weather_code, uv_index = 1, None
    condition_label = "Unknown"

# ─── Sun Coverage ────────────────────────────────────────────────────────────────
if elevation <= 0:
    sun_coverage = 0.0
else:
    rad_pct = min(100.0, (direct_rad / 800.0) * 100.0)
    if 180 <= azimuth <= 230:
        geo = 0.6 if elevation < 40 else 1.0
    elif 230 < azimuth <= 300:
        geo = 0.0 if elevation < 30 else min(1.0, (elevation - 30) / 30)
    else:
        geo = 1.0 if elevation >= 15 else elevation / 15
    sun_coverage = max(0.0, min(100.0, rad_pct * geo))

# ─── Feels Like (API + small radiant boost) ──────────────────────────────────────
display_feels = feels_like
if sun_coverage > 60 and direct_rad > 400 and wind_speed < 12 and cloud_cover < 30:
    boost = 5.0 * (sun_coverage / 100.0) * max(0.0, (12 - wind_speed) / 12)
    display_feels = feels_like + boost

# ─── Verdict ─────────────────────────────────────────────────────────────────────
def get_verdict(elev, sun, wind, feels, clouds, precip):
    if precip > 0.2:
        return "bad",  "🌧️", "Precipitation detected.", f"{precip:.1f} mm falling — skip the terrace today."
    if elev <= 0:
        return "night","🌙", "Sun is below the horizon.", "The terrace is dark right now."
    if clouds > 75:
        return "bad",  "☁️", "Heavily overcast.", f"{clouds}% cloud cover — no direct sun expected."
    if sun < 15:
        return "bad",  "🏢", "Mostly in shadow.", f"Only {sun:.0f}% sun — neighboring towers are blocking the light."
    if feels < 45:
        return "bad",  "🥶", "Sunny but too cold.", f"Feels like {feels:.0f}°F — not terrace weather."
    if feels > 88:
        return "bad",  "🥵", "Too hot.", f"Feels like {feels:.0f}°F — it's a scorcher up there. Stay inside."
    if wind > 18 and feels < 60:
        return "ok",   "💨", "Sunny but windy.", f"{wind:.0f} mph winds — feels like {feels:.0f}°F. Bring a layer."
    if sun >= 60 and feels >= 60:
        return "great","☀️", "GREAT TERRACE CONDITIONS!", f"{sun:.0f}% of the patio has direct sunlight, winds are calm, and it feels like {feels:.0f}°F. Perfect time to go up!"
    return "ok", "🌤", "Decent conditions.", f"Partial sun ({sun:.0f}%), feels like {feels:.0f}°F."

level, icon, bold_text, detail_text = get_verdict(
    elevation, sun_coverage, wind_speed, display_feels, cloud_cover, precipitation
)

# ─── Render ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="header-eyebrow">225 Franklin St · Boston, MA</div>', unsafe_allow_html=True)
st.markdown('<div class="header-title">Terrace Sun Tracker</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="header-sub">5th Floor Amenity Deck · {now_boston.strftime("%A, %B %d · %I:%M %p")}</div>',
    unsafe_allow_html=True
)

if not api_ok:
    st.markdown(
        '<div class="api-warn">⚠️ Live data stream interrupted — showing estimated values. See debug panel below.</div>',
        unsafe_allow_html=True
    )

# Sun coverage hero card
bar_color = "linear-gradient(90deg, #f5a623, #ffde47)" if sun_coverage > 15 else "#e8e0d0"
st.markdown(f"""
<div class="sun-arc-container">
    <div class="sun-pct-label">Terrace Sun Coverage</div>
    <div class="sun-pct-value">{sun_coverage:.0f}%</div>
    <div class="sun-track">
        <div class="sun-fill" style="width:{sun_coverage:.0f}%; background:{bar_color};"></div>
    </div>
    <div class="sun-meta">Solar radiation {direct_rad:.0f} W/m² · Sun elevation {elevation:.1f}° · Azimuth {azimuth:.0f}°</div>
</div>
""", unsafe_allow_html=True)

# Three metric cards
st.markdown(f"""
<div class="metrics-grid">
    <div class="metric-card">
        <div class="metric-card-label">Air Temp</div>
        <div class="metric-card-value">{air_temp:.0f}°</div>
        <div class="metric-card-sub">Fahrenheit</div>
    </div>
    <div class="metric-card">
        <div class="metric-card-label">Feels Like</div>
        <div class="metric-card-value">{display_feels:.0f}°</div>
        <div class="metric-card-sub">Incl. radiant adj.</div>
    </div>
    <div class="metric-card">
        <div class="metric-card-label">Wind</div>
        <div class="metric-card-value">{wind_speed:.0f}</div>
        <div class="metric-card-sub">mph · gusts {wind_gusts:.0f}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Detail chips
chips = [
    f"💧 {humidity:.0f}% humidity",
    f"☁️ {cloud_cover}% cloud cover",
    f"{condition_label}",
]
if uv_index is not None:
    chips.append(f"🕶️ UV: {uv_index:.0f}")
if precipitation > 0:
    chips.append(f"🌧 {precipitation:.1f} mm precip")
chips.append("📡 Open-Meteo" if api_ok else "📡 Fallback data")

chips_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
st.markdown(f'<div class="chips-row">{chips_html}</div>', unsafe_allow_html=True)

# Verdict
st.markdown(f"""
<div class="verdict-box verdict-{level}">
    {icon} <span class="verdict-bold">{bold_text}</span> {detail_text}
</div>
""", unsafe_allow_html=True)

# Debug
with st.expander("🔧 Debug: API response"):
    st.json(debug_info)
