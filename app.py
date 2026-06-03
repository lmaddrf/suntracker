import streamlit as st
import pandas as pd
from pvlib import solarposition
import requests
from datetime import datetime
import pytz

# 1. Page Configuration
st.set_page_config(page_title="225 Franklin Sun Tracker", page_icon="☀️", layout="centered")
st.title("☀️ 225 Franklin Terrace Sun Tracker")
st.markdown("### 5th Floor Amenity Terrace — Corner of Franklin & Pearl")

# 2. Coordinates & Constants
LAT, LON = 42.3556, -71.0565
BOSTON_TZ = pytz.timezone('America/New_York')
now_boston = datetime.now(BOSTON_TZ)

st.write(f"**Current Local Time:** {now_boston.strftime('%I:%M %p | %B %d, %Y')}")

# 3. Step 1: Calculate Sun Geometry
solpos = solarposition.get_solarposition(pd.Timestamp(now_boston), LAT, LON)
elevation = float(solpos['apparent_elevation'].iloc[0])
azimuth = float(solpos['azimuth'].iloc[0])

# 4. Step 2: Fetch Live Weather, Wind, and Wind Chill (Open-Meteo API)
# We fetch temperature, wind speed, wind chill (apparent temperature), and cloud cover
weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m,relative_humidity_2m,apparent_temperature,cloud_cover,wind_speed_10m&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=America%2FNew_York"

try:
    weather_response = requests.get(weather_url).json()
    current_data = weather_response['current']
    cloud_cover = current_data['cloud_cover']
    air_temp = current_data['temperature_2m']
    wind_speed = current_data['wind_speed_10m']
    wind_chill = current_data['apparent_temperature'] # Apparent temp factors in wind chill / humidity
except:
    cloud_cover, air_temp, wind_speed, wind_chill = 0, 65, 5, 65 # Fallbacks if API fails

# 5. Step 3: Calculate Sun Coverage % Based on Urban Geometry
# 5th floor at Franklin & Pearl means massive towers block the West/Southwest completely when low.
sun_coverage = 0.0

if elevation <= 0:
    sun_coverage = 0.0  # Nighttime
elif cloud_cover > 85:
    sun_coverage = 0.0  # Completely overcast, no direct sun shadows
else:
    # Basic geometric modeling of surrounding towers:
    if 180 <= azimuth <= 230:  # Sun is South/Southwest
        if elevation < 45:
            sun_coverage = 10.0  # Mostly blocked by nearby towers, just a tiny sliver
        else:
            sun_coverage = 90.0  # High enough to clear the roofs
    elif 230 < azimuth <= 300:  # Sun is moving West (One Federal St area)
        if elevation < 35:
            sun_coverage = 0.0   # Total shadow
        elif 35 <= elevation <= 55:
            # As the sun transitions behind the edge of the tower, coverage grows
            sun_coverage = float((elevation - 35) / 20 * 100)
        else:
            sun_coverage = 100.0
    else:
        # Morning/Early afternoon paths have clearer corridors over Post Office Square
        if elevation < 20:
            sun_coverage = float((elevation / 20) * 100)
        else:
            sun_coverage = 100.0

# Bound coverage between 0 and 100
sun_coverage = max(0.0, min(100.0, sun_coverage))

# 6. Step 4: Display Dashboard Metrics
st.markdown("---")
col1, col2, col3 = st.columns(3)
col1.metric("Sun Deck Coverage", f"{sun_coverage:.0f}%")
col2.metric("Wind Speed", f"{wind_speed:.1f} mph")
col3.metric("Wind Chill / Feels Like", f"{wind_chill:.1f}°F")

st.markdown("---")

# 7. Smart Notification Logic
if elevation <= 0:
    st.error("🌙 **It's currently dark.** The sun is below the horizon.")
elif cloud_cover > 70:
    st.info("☁️ **Overcast skies.** Even if the geometric path is clear, it's currently gray and cloudy outside.")
elif sun_coverage < 20:
    st.warning(f"🏢 **Tiny Sliver Alert ({sun_coverage:.0f}% Sun).** The sun is mostly blocked by neighboring towers. The patio is almost entirely in the shade and likely chilly!")
elif wind_speed > 15 and wind_chill < 60:
    st.warning(f"💨 **Sunny but Windy! ({sun_coverage:.0f}% Sun).** The sun is hitting the deck, but with a {wind_speed:.0f} mph wind, it feels like {wind_chill:.0f}°F. Bring a jacket!")
else:
    st.success(f"☀️ **GREAT TERRACE CONDITIONS!** {sun_coverage:.0f}% of the patio has direct sunlight, winds are calm, and it feels like {wind_chill:.0f}°F. Perfect time to go up!")