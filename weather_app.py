from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Weather symbol mapping based on conditions
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
    """Fetch weather data for a city using Open-Meteo API (no API key needed)"""
    try:
        # Geocode the city name to get coordinates
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {"name": city_name, "count": 1, "language": "en", "format": "json"}
        geo_response = requests.get(geo_url, params=geo_params, timeout=5)
        geo_data = geo_response.json()

        if not geo_data.get("results"):
            return None, "City not found"

        location = geo_data["results"][0]
        latitude = location["latitude"]
        longitude = location["longitude"]
        display_name = f"{location['name']}, {location.get('admin1', '')}, {location.get('country', '')}"

        # Fetch weather data
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
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
            "city": display_name,
            "temperature": temperature,
            "weather_code": weather_code,
            "symbol": symbol,
        }, None

    except requests.exceptions.RequestException as e:
        return None, f"Error fetching weather data: {str(e)}"
    except Exception as e:
        return None, f"Error: {str(e)}"

@app.route("/")
def index():
    """Display the main form"""
    return render_template("index.html")

@app.route("/get_weather", methods=["POST"])
def get_weather():
    """Handle weather request"""
    city_name = request.form.get("city", "").strip()

    if not city_name:
        return render_template("result.html", error="Please enter a city name")

    weather_data, error = get_city_weather(city_name)

    if error:
        return render_template("result.html", error=error)

    return render_template(
        "result.html",
        city=weather_data["city"],
        temperature=weather_data["temperature"],
        symbol=weather_data["symbol"],
    )

@app.route("/api/weather/<city_name>")
def api_weather(city_name):
    """API endpoint to get weather as JSON"""
    weather_data, error = get_city_weather(city_name)

    if error:
        return jsonify({"error": error}), 404

    return jsonify({
        "city": weather_data["city"],
        "temperature": weather_data["temperature"],
        "symbol": weather_data["symbol"],
    })

if __name__ == "__main__":
    app.run(debug=True)
