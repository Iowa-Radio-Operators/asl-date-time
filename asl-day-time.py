import requests
import datetime
import subprocess

# CONFIGURATION
CALLSIGN = "K0IRO"
ZIP_CODE = "50208"
UNITS = "imperial"  # NWS returns Fahrenheit by default

# TTS wrapper
def speak(text):
    subprocess.run(["asl-tts", text])

# Convert ZIP to lat/lon using OpenStreetMap Nominatim
def zip_to_latlon(zip_code):
    url = f"https://nominatim.openstreetmap.org/search?postalcode={zip_code}&country=USA&format=json"
    response = requests.get(url).json()
    if not response:
        return None
    lat = response[0]["lat"]
    lon = response[0]["lon"]
    return lat, lon

# Get forecast from NWS
def get_nws_forecast(lat, lon):
    # Step 1: Get grid info
    points_url = f"https://api.weather.gov/points/{lat},{lon}"
    points = requests.get(points_url).json()
    forecast_url = points["properties"]["forecast"]

    # Step 2: Get forecast periods
    forecast = requests.get(forecast_url).json()
    periods = forecast["properties"]["periods"]
    return periods

# Build message
def build_message():
    now = datetime.datetime.now()
    hour = now.hour
    time_str = now.strftime("%I:%M %p")
    greeting = "Good morning" if hour < 12 else "Good evening"

    latlon = zip_to_latlon(ZIP_CODE)
    if not latlon:
        return f"{greeting}, this is {CALLSIGN}. The time is {time_str}. Location lookup failed."

    periods = get_nws_forecast(*latlon)
    if not periods:
        return f"{greeting}, this is {CALLSIGN}. The time is {time_str}. Weather data is unavailable."

    # Find current and daily forecast
    current_period = periods[0]
    today_high = next((p for p in periods if "High" in p["name"]), None)
    today_low = next((p for p in periods if "Low" in p["name"]), None)

    temp = current_period["temperature"]
    description = current_period["shortForecast"]

    if hour < 12 and today_high and today_low:
        weather_msg = f"The current temperature is {temp} degrees with {description}. Today's high is {today_high['temperature']} and the low is {today_low['temperature']}."
    else:
        weather_msg = f"The current temperature is {temp} degrees with {description}."

    return f"{greeting}, this is {CALLSIGN}. The time is {time_str}. {weather_msg}"

# Run it
if __name__ == "__main__":
    message = build_message()
    print("Speaking:", message)
    speak(message)