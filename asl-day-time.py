import requests
import datetime
import subprocess

# CONFIGURATION
CALLSIGN = "K0IRO"
ZIP_CODE = "50208"           # Newton, IA
NODE_ID = 656831              # AllStar node number
USER_AGENT_EMAIL = "calvin@k0iro.com"  # Used for Nominatim API header

# TTS wrapper
def speak(text):
    subprocess.run(["asl-tts", "-n", str(NODE_ID), "-t", text])

# Greeting logic
def get_greeting(hour):
    if hour < 12:
        return "Good morning"
    elif hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"

# Normalize forecast phrasing
def normalize_forecast(description):
    desc = description.lower()
    if "rain" in desc:
        return "rain"
    elif "snow" in desc:
        return "snow"
    elif "sun" in desc or "clear" in desc:
        return "sunny skies"
    elif "cloud" in desc:
        return "cloudy skies"
    elif "storm" in desc:
        return "stormy weather"
    else:
        return description

# Convert ZIP to lat/lon using OpenStreetMap
def zip_to_latlon(zip_code):
    url = f"https://nominatim.openstreetmap.org/search?postalcode={zip_code}&country=USA&format=json"
    headers = {
        "User-Agent": f"AllStarWeatherBot/1.0 ({USER_AGENT_EMAIL})"
    }
    response = requests.get(url, headers=headers)
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        print("Failed to decode JSON from Nominatim")
        return None
    if not data:
        print("No location data returned for ZIP")
        return None
    return data[0]["lat"], data[0]["lon"]

# Get forecast and humidity from NWS
def get_nws_forecast(lat, lon):
    try:
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        points = requests.get(points_url).json()
        forecast_url = points["properties"]["forecast"]
        observation_url = points["properties"]["observationStations"]

        forecast = requests.get(forecast_url).json()
        periods = forecast["properties"]["periods"]

        obs_response = requests.get(observation_url).json()
        station_id = obs_response["features"][0]["properties"]["stationIdentifier"]
        obs_data = requests.get(f"https://api.weather.gov/stations/{station_id}/observations/latest").json()
        humidity = obs_data["properties"]["relativeHumidity"]["value"]

        return periods, humidity
    except Exception as e:
        print("Error fetching NWS data:", e)
        return None, None

# Build the spoken message
def build_message():
    now = datetime.datetime.now()
    hour = now.hour
    greeting = get_greeting(hour)
    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%A %B %-d")

    latlon = zip_to_latlon(ZIP_CODE)
    if not latlon:
        return f"{greeting}, this is the {CALLSIGN} Repeater. Today is {date_str} and time is {time_str}. Location lookup failed."

    periods, humidity = get_nws_forecast(*latlon)
    if not periods:
        return f"{greeting}, this is the {CALLSIGN} Repeater. Today is {date_str} and time is {time_str}. Weather data is unavailable."

    current = periods[0]
    today_high = next((p for p in periods if "High" in p["name"]), None)
    today_low = next((p for p in periods if "Low" in p["name"]), None)

    temp = current["temperature"]
    description = normalize_forecast(current["shortForecast"])
    humidity_msg = f" The humidity is {int(humidity)} percent." if humidity and humidity > 60 else ""

    if hour < 12 and today_high and today_low:
        weather_msg = f"The current temperature is {temp} degrees with {description}.{humidity_msg} Today's high is {today_high['temperature']} and the low is {today_low['temperature']}."
    else:
        weather_msg = f"The current temperature is {temp} degrees with {description}.{humidity_msg}"

    return f"{greeting}, this is the {CALLSIGN} Repeater. Today is {date_str} and time is {time_str}. {weather_msg}"

# Run it
if __name__ == "__main__":
    message = build_message()
    print("Speaking:", message)
    speak(message)