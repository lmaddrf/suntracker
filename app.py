import streamlit as st
import pandas as pd
from pvlib import solarposition
import requests
from datetime import datetime, timedelta
import pytz

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="225 Franklin Terrace Sun Tracker",
    page_icon="☀️",
    layout="centered"
)

# ─── Auto-refresh every 15 minutes ──────────────────────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=15 * 60 * 1000, key="autorefresh")
except ImportError:
    pass

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
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
    font-family: 'Inter', sans-serif;
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
    font-family: 'Inter', sans-serif;
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
.sun-fill { height: 8px; border-radius: 999px; }
.sun-meta { font-size: 0.78rem; color: #b07d2a; opacity: 0.8; }

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
    font-family: 'Inter', sans-serif;
    font-size: 2.4rem;
    font-weight: 700;
    color: #1c1c1c;
    line-height: 1;
    margin-bottom: 0.3rem;
}
.metric-card-sub { font-size: 0.75rem; color: #bbb; }

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
    margin-bottom: 1.5rem;
}
.verdict-great { background: linear-gradient(135deg, #edfaf3, #d6f5e6); border: 1px solid #a8e6c2; color: #1a5c3a; }
.verdict-ok    { background: linear-gradient(135deg, #fdfbec, #faf3d0); border: 1px solid #e8d87a; color: #6b5300; }
.verdict-bad   { background: linear-gradient(135deg, #fdf0f0, #fde0e0); border: 1px solid #f0b8b8; color: #7a1a1a; }
.verdict-night { background: linear-gradient(135deg, #f0f0fd, #e4e4fa); border: 1px solid #c0c0ee; color: #2a2a6a; }
.verdict-bold  { font-weight: 700; }

.section-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #aaa;
    margin-bottom: 0.9rem;
    margin-top: 0.5rem;
}

.hourly-grid {
    display: flex;
    gap: 4px;
    align-items: flex-end;
    margin-bottom: 0.5rem;
    height: 48px;
}
.hour-bar-wrap { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 3px; }
.hour-bar { width: 100%; border-radius: 3px 3px 0 0; min-height: 4px; }
.hour-label { font-size: 0.6rem; color: #aaa; white-space: nowrap; }
.hour-label-bold { font-size: 0.6rem; color: #1c1c1c; font-weight: 600; white-space: nowrap; }
.best-window-note { font-size: 0.8rem; color: #555; margin-top: 0.4rem; }
.best-window-highlight { font-weight: 600; color: #1c1c1c; }

.tomorrow-card {
    background: #ffffff;
    border: 1px solid #ebebeb;
    border-radius: 14px;
    padding: 1.1rem 1.4rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
}
.tomorrow-left { display: flex; flex-direction: column; gap: 0.2rem; }
.tomorrow-date { font-size: 0.75rem; color: #aaa; font-weight: 500; text-transform: uppercase; letter-spacing: 0.1em; }
.tomorrow-summary { font-size: 1rem; font-weight: 600; color: #1c1c1c; }
.tomorrow-detail { font-size: 0.82rem; color: #888; }
.tomorrow-right { text-align: right; }
.tomorrow-temp { font-size: 2rem; font-weight: 700; color: #1c1c1c; line-height: 1; }
.tomorrow-temp-sub { font-size: 0.75rem; color: #bbb; }

.sunset-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
.sunset-card {
    flex: 1;
    background: #ffffff;
    border: 1px solid #ebebeb;
    border-radius: 14px;
    padding: 1rem 1.1rem;
    text-align: center;
}
.sunset-card-label { font-size: 0.68rem; font-weight: 500; letter-spacing: 0.12em; text-transform: uppercase; color: #aaa; margin-bottom: 0.4rem; }
.sunset-card-value { font-size: 1.4rem; font-weight: 700; color: #1c1c1c; }

.api-warn {
    font-size: 0.8rem; color: #9a6f00;
    background: #fffae8; border: 1px solid #f0d060;
    border-radius: 8px; padding: 0.5rem 1rem; margin-bottom: 1.2rem;
}
.refresh-note { font-size: 0.72rem; color: #bbb; text-align: right; margin-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# ─── Constants ───────────────────────────────────────────────────────────────────
LAT, LON = 42.3556, -71.0565
BOSTON_TZ = pytz.timezone('America/New_York')

# ─── Time & Solar ────────────────────────────────────────────────────────────────
now_boston = datetime.now(BOSTON_TZ)
today      = now_boston.date()
tomorrow   = today + timedelta(days=1)

solpos    = solarposition.get_solarposition(pd.Timestamp(now_boston), LAT, LON)
elevation = float(solpos['apparent_elevation'].iloc[0])
azimuth   = float(solpos['azimuth'].iloc[0])

# ─── Sunset / Sunrise ────────────────────────────────────────────────────────────
def get_sun_times(date):
    times = pd.date_range(
        start=BOSTON_TZ.localize(datetime(date.year, date.month, date.day, 4, 0)),
        end=BOSTON_TZ.localize(datetime(date.year, date.month, date.day, 22, 0)),
        freq='1min'
    )
    sp   = solarposition.get_solarposition(times, LAT, LON)
    elev = sp['apparent_elevation']
    sunrise = times[elev > 0][0]  if (elev > 0).any() else None
    sunset  = times[elev > 0][-1] if (elev > 0).any() else None
    return sunrise, sunset

sunrise_today, sunset_today = get_sun_times(today)
sunrise_str  = sunrise_today.strftime("%-I:%M %p") if sunrise_today else "—"
sunset_str   = sunset_today.strftime("%-I:%M %p")  if sunset_today  else "—"
daylight_str = (
    f"{int((sunset_today - sunrise_today).seconds // 3600)}h "
    f"{int((sunset_today - sunrise_today).seconds % 3600 // 60)}m"
    if sunrise_today and sunset_today else "—"
)

# ─── Weather Fetch (WeatherAPI.com) ──────────────────────────────────────────────
debug_info = {}
api_ok = False

API_KEY = st.secrets["WEATHERAPI_KEY"]

@st.cache_data(ttl=600)
def fetch_weather(api_key):
    # Current conditions
    current_url = (
        f"https://api.weatherapi.com/v1/current.json"
        f"?key={api_key}&q={LAT},{LON}&aqi=no"
    )
    # Forecast (2 days for tomorrow)
    forecast_url = (
        f"https://api.weatherapi.com/v1/forecast.json"
        f"?key={api_key}&q={LAT},{LON}&days=2&aqi=no&alerts=no"
    )
    r = requests.get(forecast_url, timeout=8)
    if r.status_code != 200:
        raise ValueError(f"HTTP {r.status_code}: {r.text[:200]}")
    return r.json()

try:
    data = fetch_weather(API_KEY)
    cur  = data['current']
    loc  = data['location']

    air_temp        = cur['temp_f']
    feels_like      = cur['feelslike_f']
    humidity        = cur['humidity']
    cloud_cover     = cur['cloud']
    wind_speed      = cur['wind_mph']
    wind_gusts      = cur['gust_mph']
    direct_rad      = cur.get('solar_w_per_m2', cur.get('vis_miles', 0) * 50)
    uv_index        = cur.get('uv', None)
    precipitation   = cur.get('precip_mm', 0)
    condition_label = cur['condition']['text']
    condition_code  = cur['condition']['code']
    api_ok = True
    debug_info['http_status'] = 200
    debug_info['raw'] = {
        'air_temp': air_temp, 'feels_like': feels_like,
        'humidity': humidity, 'cloud_cover': cloud_cover,
        'wind_speed': wind_speed, 'wind_gusts': wind_gusts,
        'uv_index': uv_index, 'precipitation': precipitation,
        'condition': condition_label,
    }

    # Hourly data for today
    forecast_days = data.get('forecast', {}).get('forecastday', [])
    today_fc  = forecast_days[0] if len(forecast_days) > 0 else None
    tomorrow_fc = forecast_days[1] if len(forecast_days) > 1 else None

    today_hourly = today_fc['hour'] if today_fc else []
    h_times    = [h['time'] for h in today_hourly]
    h_feels    = [h['feelslike_f'] for h in today_hourly]
    h_wind     = [h['wind_mph'] for h in today_hourly]
    h_clouds   = [h['cloud'] for h in today_hourly]
    h_rad      = [h.get('solar_w_per_m2', (100 - h['cloud']) * 6) for h in today_hourly]
    h_precip_p = [h.get('chance_of_rain', 0) for h in today_hourly]

    # Tomorrow
    if tomorrow_fc:
        td = tomorrow_fc['day']
        tmr_temp     = td['maxtemp_f']
        tmr_feels    = td['avgtemp_f']
        tmr_wind     = td['maxwind_mph']
        tmr_condition = td['condition']['text']
        tmr_condition_code = td['condition']['code']
        tmr_precip_p = td.get('daily_chance_of_rain', 0)
    else:
        tmr_temp = tmr_feels = tmr_wind = tmr_condition = tmr_precip_p = None
        tmr_condition_code = 1000

except Exception as e:
    debug_info['exception'] = str(e)
    air_temp, feels_like, humidity = 68.0, 66.0, 55
    cloud_cover, wind_speed, wind_gusts = 25, 8.0, 12.0
    direct_rad, precipitation = 350, 0
    uv_index = None
    condition_label = "Unknown"
    h_times = h_feels = h_wind = h_clouds = h_rad = h_precip_p = []
    tmr_temp = tmr_feels = tmr_wind = tmr_condition = tmr_precip_p = None
    tmr_condition_code = 1000

# ─── WeatherAPI condition code → emoji ───────────────────────────────────────────
def condition_emoji(code):
    sunny   = {1000}
    pcloudy = {1003}
    cloudy  = {1006, 1009}
    fog     = {1030, 1135, 1147}
    rain    = {1063,1072,1150,1153,1168,1171,1180,1183,1186,1189,1192,1195,1198,1201,1240,1243,1246}
    snow    = {1066,1069,1114,1117,1204,1207,1210,1213,1216,1219,1222,1225,1255,1258}
    thunder = {1087,1273,1276,1279,1282}
    if code in sunny:   return "☀️"
    if code in pcloudy: return "⛅"
    if code in cloudy:  return "☁️"
    if code in fog:     return "🌫"
    if code in rain:    return "🌧"
    if code in snow:    return "❄️"
    if code in thunder: return "⛈"
    return "🌤"

# ─── Sun Coverage ────────────────────────────────────────────────────────────────
def calc_sun_coverage(elev, az, rad):
    if elev <= 0:
        return 0.0
    rad_pct = min(100.0, (rad / 800.0) * 100.0)

    if 85 <= az <= 112:
        geo = 0.0 if elev < 75 else 1.0
elif 112 < az <= 145:
    geo = min(0.15, (az - 112) / 33 * 0.15)
    elif 70 <= az < 80:
        geo = 0.0 if elev < 60 else 0.5
    elif 145 < az <= 230:
        geo = 0.5 if elev < 40 else 1.0
    elif 230 < az <= 300:
        geo = 0.0 if elev < 30 else min(1.0, (elev - 30) / 30)
    else:
        geo = 1.0 if elev >= 20 else elev / 20

    geo = geo if geo is not None else 0.0
    return max(0.0, min(100.0, rad_pct * geo))
sun_coverage = calc_sun_coverage(elevation, azimuth, direct_rad)

# ─── Feels Like with radiant boost ───────────────────────────────────────────────
display_feels = feels_like
if sun_coverage > 60 and direct_rad > 400 and wind_speed < 12 and cloud_cover < 30:
    boost = 5.0 * (sun_coverage / 100.0) * max(0.0, (12 - wind_speed) / 12)
    display_feels = feels_like + boost

# ─── Terrace score for hourly ranking ────────────────────────────────────────────
def terrace_score(feels, wind, clouds, rad, precip_p):
    if precip_p > 40 or clouds > 80:
        return 0
    temp_score  = max(0, min(100, (feels - 45) / (85 - 45) * 100)) if feels <= 88 else max(0, 100 - (feels - 88) * 10)
    wind_score  = max(0, 100 - wind * 3)
    sun_score   = min(100, rad / 6)
    cloud_score = max(0, 100 - clouds)
    return (temp_score * 0.4 + wind_score * 0.25 + sun_score * 0.2 + cloud_score * 0.15)

# ─── Build today's hourly windows ────────────────────────────────────────────────
today_hours = []
now_hour = now_boston.replace(minute=0, second=0, microsecond=0)

for i, t_str in enumerate(h_times):
    try:
        t = BOSTON_TZ.localize(datetime.strptime(t_str, "%Y-%m-%d %H:%M"))
    except:
        continue
    if t < now_hour:
        continue
    if t.hour < 7 or t.hour > 20:
        continue
    score = terrace_score(
        h_feels[i]    if i < len(h_feels)    else 70,
        h_wind[i]     if i < len(h_wind)     else 10,
        h_clouds[i]   if i < len(h_clouds)   else 30,
        h_rad[i]      if i < len(h_rad)      else 200,
        h_precip_p[i] if i < len(h_precip_p) else 0,
    )
    today_hours.append({'time': t, 'score': score,
                        'feels': h_feels[i] if i < len(h_feels) else 70,
                        'wind':  h_wind[i]  if i < len(h_wind)  else 10})

best_window_start = None
best_window_score = -1
for j in range(len(today_hours) - 1):
    combined = today_hours[j]['score'] + today_hours[j+1]['score']
    if combined > best_window_score:
        best_window_score = combined
        best_window_start = today_hours[j]['time']

# ─── Tomorrow verdict ────────────────────────────────────────────────────────────
def tomorrow_verdict(feels, wind, condition, precip_p):
    if feels is None:
        return "No forecast available."
    if precip_p and precip_p > 50:
        return f"Likely wet ({precip_p:.0f}% chance of rain) — plan accordingly."
    if feels > 88:
        return f"Feels like {feels:.0f}°F — probably too hot for the terrace."
    if feels < 45:
        return f"Feels like {feels:.0f}°F — too cold."
    if wind and wind > 20:
        return f"Windy day ({wind:.0f} mph max) — breezy up top."
    return f"Looks good — feels like {feels:.0f}°F."

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

# ═══════════════════════════════════════════════════════════════════════════════
# RENDER
# ═══════════════════════════════════════════════════════════════════════════════

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

# ── Sun coverage hero ──
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

# ── Three metric cards ──
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

# ── Chips ──
chips = [
    f"💧 {humidity:.0f}% humidity",
    f"☁️ {cloud_cover}% cloud cover",
    f"{condition_label}",
]
if uv_index is not None:
    chips.append(f"🕶️ UV: {uv_index:.0f}")
if precipitation > 0:
    chips.append(f"🌧 {precipitation:.1f} mm precip")
chips.append("📡 WeatherAPI" if api_ok else "📡 Fallback data")
chips_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
st.markdown(f'<div class="chips-row">{chips_html}</div>', unsafe_allow_html=True)

# ── Verdict ──
st.markdown(f"""
<div class="verdict-box verdict-{level}">
    {icon} <span class="verdict-bold">{bold_text}</span> {detail_text}
</div>
""", unsafe_allow_html=True)

# ── Sunrise / Sunset ──
st.markdown('<div class="section-label">Today\'s Sun</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="sunset-row">
    <div class="sunset-card">
        <div class="sunset-card-label">🌅 Sunrise</div>
        <div class="sunset-card-value">{sunrise_str}</div>
    </div>
    <div class="sunset-card">
        <div class="sunset-card-label">🌇 Sunset</div>
        <div class="sunset-card-value">{sunset_str}</div>
    </div>
    <div class="sunset-card">
        <div class="sunset-card-label">⏱ Daylight</div>
        <div class="sunset-card-value">{daylight_str}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Best time today ──
if today_hours:
    st.markdown('<div class="section-label">Best Time Today</div>', unsafe_allow_html=True)
    max_score = max(h['score'] for h in today_hours) or 1

    bars_html = ""
    for h in today_hours:
        pct     = int((h['score'] / max_score) * 100)
        is_best = best_window_start and h['time'] == best_window_start
        bar_bg  = "#f5a623" if h['score'] > 60 else ("#c8d8e8" if h['score'] > 20 else "#ebebeb")
        lbl_cls = "hour-label-bold" if is_best else "hour-label"
        label   = h['time'].strftime("%-I%p").lower()
        bars_html += f"""
        <div class="hour-bar-wrap">
            <div class="hour-bar" style="height:{max(4, pct // 2)}px; background:{bar_bg};"></div>
            <div class="{lbl_cls}">{label}</div>
        </div>"""

    best_note = ""
    if best_window_start:
        best_end  = best_window_start + timedelta(hours=2)
        best_note = (
            f'<div class="best-window-note">Best window: '
            f'<span class="best-window-highlight">'
            f'{best_window_start.strftime("%-I:%M %p")} – {best_end.strftime("%-I:%M %p")}'
            f'</span></div>'
        )

    st.markdown(f"""
    <div style="background:#ffffff; border:1px solid #ebebeb; border-radius:14px; padding:1.25rem 1.1rem; margin-bottom:1.5rem;">
        <div class="hourly-grid">{bars_html}</div>
        {best_note}
    </div>
    """, unsafe_allow_html=True)

# ── Tomorrow at a glance ──
if tmr_temp is not None:
    tmr_emoji        = condition_emoji(tmr_condition_code)
    tmr_summary_text = tomorrow_verdict(tmr_feels, tmr_wind, tmr_condition, tmr_precip_p)
    st.markdown('<div class="section-label">Tomorrow</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="tomorrow-card">
        <div class="tomorrow-left">
            <div class="tomorrow-date">{tomorrow.strftime("%A, %B %d")}</div>
            <div class="tomorrow-summary">{tmr_emoji} {tmr_condition}</div>
            <div class="tomorrow-detail">{tmr_summary_text}</div>
        </div>
        <div class="tomorrow-right">
            <div class="tomorrow-temp">{tmr_temp:.0f}°</div>
            <div class="tomorrow-temp-sub">High · feels {tmr_feels:.0f}°</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Refresh note ──
st.markdown(
    f'<div class="refresh-note">Auto-refreshes every 15 min · Last update: {now_boston.strftime("%I:%M %p")}</div>',
    unsafe_allow_html=True
)

# ── Debug ──
with st.expander("🔧 Debug: API response"):
    st.json(debug_info)
