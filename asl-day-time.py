#!/usr/bin/env python3
import requests
import datetime
import subprocess
import os

# CONFIGURATION
CALLSIGN = "K0IRO"
ZIP_CODE = "50168"           # Mingo, IA
NODE_ID = 656830             # AllStar node number
USER_AGENT_EMAIL = "calvin@k0iro.com"  # Used for API header (required)

def speak(text):
    """Hand off text to asl-tts with a safe environment."""
    if not text.strip():
        return
    env = os.environ.copy()
    # Force USER so asl-tts passes its check
    env["USER"] = "asterisk"
    # Ensure PATH includes /usr/sbin so asterisk is found
    env["PATH"] = "/usr/sbin:/usr/bin:/bin"
    subprocess.run(
        ["asl-tts", "-n", str(NODE_ID), "-t", text],
        env=env
    )

def get_greeting(hour):
    if hour < 12:
        return "Good morning"
    elif hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"

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

def get_day_with_suffix(day):
    if 11 <= day <= 13:
        return f"{day}th"
    last_digit = day % 10
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(last_digit, "th")
    return f"{day}{suffix}"

def zip_to_latlon(zip_code):
    url = f"https://nominatim.openstreetmap.org/search?postalcode={zip_code}&country=USA&format=json"
    headers = {"User-Agent": f"AllStarWeatherBot/1.0 ({USER_AGENT_EMAIL})"}
    response = requests.get(url, headers=headers)
    data = response.json()
    if not data:
        return None
    return data[0]["lat"], data[0]["lon"]

def get_nws_forecast(lat, lon):
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
    temperature_c = obs_data["properties"]["temperature"]["value"]

    return periods, humidity, temperature_c

def get_high_low(periods):
    high = next((p for p in periods if p["isDaytime"]), None)
    low = next((p for p in periods if not p["isDaytime"]), None)
    return high, low

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

    periods, humidity, temperature_c = get_nws_forecast(*latlon)
    if not periods or temperature_c is None:
        return f"{greeting}, this is the {CALLSIGN} Repeater. Today is {date_str} and time is {time_str}. Weather data is unavailable."

    high, low = get_high_low(periods)
    current_forecast = normalize_forecast(periods[0]["shortForecast"])
    temp_f = round((temperature_c * 9/5) + 32) if temperature_c is not None else "unknown"
    humidity_msg = f" The humidity is {int(humidity)} percent." if humidity and humidity > 60 else ""

    weather_msg = f"The current temperature is {temp_f} degrees Fahrenheit with {current_forecast}.{humidity_msg}"

    if hour < 12 and high and low:
        weather_msg += f" Today's high is {high['temperature']} and the low is {low['temperature']}."
    if hour >= 18 and len(periods) > 2:
        tomorrow = periods[2]
        tomorrow_forecast = normalize_forecast(tomorrow["shortForecast"])
        weather_msg += f" Tomorrow's forecast is {tomorrow_forecast} with a high of {tomorrow['temperature']} degrees."

    return f"{greeting}, this is the {CALLSIGN} Repeater. Today is {date_str} and time is {time_str}. {weather_msg}"

if __name__ == "__main__":
    message = build_message()
    print("Speaking:", message)
    speak(message)