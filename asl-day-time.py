import requests
import datetime
import subprocess

# CONFIGURATION
CALLSIGN = "K0IRO"
ZIP_CODE = "50208"           # Newton, IA
NODE_ID = 656831             # AllStar node number
USER_AGENT_EMAIL = "calvin@k0iro.com"  # Used for API header (required)

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

# Add ordinal suffix to day
def get_day_with_suffix(day):
    if 11 <= day <= 13:
        return f"{day}th"
    last_digit = day % 10
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(last_digit, "th")
    return f"{day}{suffix}"

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

# Get forecast and observation data from NWS
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
        temperature = obs_data["properties"]["temperature"]["value"]

        return periods, humidity, temperature
    except Exception as e:
        print("Error fetching NWS data:", e)
        return None, None, None

# Get first daytime and nighttime periods
def get_high_low(periods):
    high = next((p for p in periods if p["isDaytime"]), None)
    low = next((p for p in periods if not p["isDaytime"]), None)
    return high, low

# Build the spoken message
def build_message():
    now = datetime.datetime.now()
    hour = now.hour
    greeting = get_greeting(hour)
    time_str = now.strftime("%I:%M %p")
    weekday = now.strftime("%A")
    month = now.strftime("%B")
    day_with_suffix = get_day_with_suffix(now.day)
    date_str = f"{weekday} {month} {day_with_suffix}"

    latlon = zip_to_latlon(ZIP_CODE)
    if not latlon:
        return f"{greeting}, this is the {CALLSIGN} Repeater. Today is {date_str} and time is {time_str}. Location lookup failed."

    periods, humidity, temperature = get_nws_forecast(*latlon)
    if not periods or temperature is None:
        return f"{greeting}, this is the {CALLSIGN} Repeater. Today is {date_str} and time is {time_str}. Weather data is unavailable."

    high, low = get_high_low(periods)
    current_forecast = normalize_forecast(periods[0]["shortForecast"])
    temp_f = round((temperature * 9/5) + 32) if temperature is not None else "unknown"
    humidity_msg = f" The humidity is {int(humidity)} percent." if humidity and humidity > 60 else ""

    # Base message
    weather_msg = f"The current temperature is {temp_f} degrees Fahrenheit with {current_forecast}.{humidity_msg}"

    # Add high/low in morning
    if hour < 12 and high and low:
        weather_msg += f" Today's high is {high['temperature']} and the low is {low['temperature']}."

    # Add tomorrow's forecast in evening
    if hour >= 18 and len(periods) > 2:
        tomorrow = periods[2]
        tomorrow_forecast = normalize_forecast(tomorrow["shortForecast"])
        weather_msg += f" Tomorrow's forecast is {tomorrow_forecast} with a high of {tomorrow['temperature']} degrees."

    return f"{greeting}, this is the {CALLSIGN} Repeater. Today is {date_str} and time is {time_str}. {weather_msg}"

# Run it
if __name__ == "__main__":
    message = build_message()
    print("Speaking:", message)
    speak(message)