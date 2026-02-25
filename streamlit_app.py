import streamlit as st
import requests
from datetime import datetime

# Weather symbol mapping
WEATHER_SYMBOLS = {
    "clear": "☀️",
    "partly_cloudy": "⛅",
    "cloudy": "☁️",
    "overcast": "☁️",
    "rain": "🌧️",
    "drizzle": "🌦️",
    "thunderstorm": "⛈️",
    "snow": "❄️",
    "sleet": "🌨️",
    "mist": "🌫️",
    "fog": "🌫️",
}

def get_weather_symbol(weather_code):
    """Convert WMO weather code to symbol"""
    if weather_code == 0:
        return WEATHER_SYMBOLS.get("clear", "☀️")
    elif weather_code == 1 or weather_code == 2:
        return WEATHER_SYMBOLS.get("partly_cloudy", "⛅")
    elif weather_code == 3:
        return WEATHER_SYMBOLS.get("overcast", "☁️")
    elif weather_code == 45 or weather_code == 48:
        return WEATHER_SYMBOLS.get("fog", "🌫️")
    elif weather_code in [51, 53, 55]:
        return WEATHER_SYMBOLS.get("drizzle", "🌦️")
    elif weather_code in [61, 63, 65]:
        return WEATHER_SYMBOLS.get("rain", "🌧️")
    elif weather_code in [71, 73, 75, 77, 85, 86]:
        return WEATHER_SYMBOLS.get("snow", "❄️")
    elif weather_code in [80, 81, 82]:
        return WEATHER_SYMBOLS.get("rain", "🌧️")
    elif weather_code in [95, 96, 99]:
        return WEATHER_SYMBOLS.get("thunderstorm", "⛈️")
    else:
        return "❓"

def get_city_weather(city_name):
    """Fetch weather data for a city with forecast"""
    try:
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {"name": city_name, "count": 5, "language": "en", "format": "json"}
        geo_response = requests.get(geo_url, params=geo_params, timeout=5)
        geo_data = geo_response.json()

        if not geo_data.get("results"):
            return None, None, "City not found"

        location = geo_data["results"][0]
        latitude = location["latitude"]
        longitude = location["longitude"]
        display_name = f"{location['name']}, {location.get('admin1', '')}, {location.get('country', '')}"

        # Get nearby cities (first 2 alternatives from results)
        nearby_cities = []
        for i in range(1, min(3, len(geo_data["results"]))):
            nearby = geo_data["results"][i]
            nearby_name = f"{nearby['name']}, {nearby.get('admin1', '')}, {nearby.get('country', '')}"
            nearby_cities.append({
                "name": nearby_name,
                "lat": nearby["latitude"],
                "lon": nearby["longitude"]
            })

        # Fetch current weather + forecast
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "weather_code,temperature_2m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
            "timezone": "auto",
        }
        weather_response = requests.get(weather_url, params=weather_params, timeout=5)
        weather_data = weather_response.json()

        current_weather = weather_data["current"]
        weather_code = current_weather["weather_code"]
        temperature = current_weather["temperature_2m"]
        symbol = get_weather_symbol(weather_code)

        # Get 2-day forecast
        daily = weather_data["daily"]
        forecast = []
        for i in range(1, min(3, len(daily["time"]))):  # Next 2 days
            date = datetime.fromisoformat(daily["time"][i]).strftime("%a, %b %d")
            weather_code_day = daily["weather_code"][i]
            temp_max = daily["temperature_2m_max"][i]
            temp_min = daily["temperature_2m_min"][i]
            symbol_day = get_weather_symbol(weather_code_day)
            forecast.append({
                "date": date,
                "symbol": symbol_day,
                "max_temp": temp_max,
                "min_temp": temp_min
            })

        return {
            "city": display_name,
            "temperature": temperature,
            "weather_code": weather_code,
            "symbol": symbol,
            "forecast": forecast
        }, nearby_cities, None

    except requests.exceptions.RequestException as e:
        return None, None, f"Error fetching weather data: {str(e)}"
    except Exception as e:
        return None, None, f"Error: {str(e)}"

def get_nearby_city_weather(lat, lon, city_name):
    """Fetch weather for a nearby city"""
    try:
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "weather_code,temperature_2m",
            "timezone": "auto",
        }
        weather_response = requests.get(weather_url, params=weather_params, timeout=5)
        weather_data = weather_response.json()

        current_weather = weather_data["current"]
        weather_code = current_weather["weather_code"]
        temperature = current_weather["temperature_2m"]
        symbol = get_weather_symbol(weather_code)

        return {
            "city": city_name,
            "temperature": temperature,
            "symbol": symbol
        }
    except:
        return None

# Streamlit UI
st.set_page_config(page_title="Weather Symbol Finder", layout="wide")
st.title("🌍 Weather Symbol Finder")
st.write("Enter a city name to see its current weather, nearby cities, and 2-day forecast")

col1, col2 = st.columns([3, 1])
with col1:
    city_name = st.text_input("Enter city name:", placeholder="e.g., London, New York, Tokyo")
with col2:
    search_button = st.button("Search", type="primary")

if city_name:
    weather_data, nearby_cities, error = get_city_weather(city_name)
    
    if error:
        st.error(f"Error: {error}")
    else:
        # Main city weather
        st.markdown("---")
        st.subheader(f"Current Weather - {weather_data['city']}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Temperature", f"{weather_data['temperature']}°C")
        with col2:
            st.markdown(f"""
            <div style='text-align: center;'>
            <p style='font-size: 80px; margin: 0;'>{weather_data['symbol']}</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.write("")
        
        # 2-Day Forecast
        st.markdown("---")
        st.subheader("2-Day Forecast")
        forecast_cols = st.columns(2)
        for i, day in enumerate(weather_data['forecast']):
            with forecast_cols[i]:
                st.write(f"**{day['date']}**")
                st.markdown(f"<div style='font-size: 60px;'>{day['symbol']}</div>", unsafe_allow_html=True)
                st.write(f"High: {day['max_temp']}°C | Low: {day['min_temp']}°C")
        
        # Nearby Cities
        if nearby_cities:
            st.markdown("---")
            st.subheader("Nearby Cities")
            nearby_weather = []
            for nearby in nearby_cities:
                weather = get_nearby_city_weather(nearby["lat"], nearby["lon"], nearby["name"])
                if weather:
                    nearby_weather.append(weather)
            
            nearby_cols = st.columns(len(nearby_weather))
            for i, weather in enumerate(nearby_weather):
                with nearby_cols[i]:
                    st.write(f"**{weather['city']}**")
                    st.markdown(f"<div style='font-size: 50px;'>{weather['symbol']}</div>", unsafe_allow_html=True)
                    st.metric("Temp", f"{weather['temperature']}°C")
