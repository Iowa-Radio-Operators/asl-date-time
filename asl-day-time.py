import datetime
import subprocess
from WunderWeather import WunderWeather

# CONFIGURATION
CALLSIGN = "W0ABC"
ZIP_CODE = "50208"  # Newton, IA
API_KEY = "your_wunderground_api_key"
UNITS = "imperial"  # 'metric' for Celsius

# TTS wrapper
def speak(text):
    subprocess.run(["asl-tts", text])

# Get weather data
def get_weather(zip_code):
    ww = WunderWeather(api_key=API_KEY)
    current = ww.conditions(zip_code=zip_code)
    forecast = ww.forecast(zip_code=zip_code)

    if not current or not forecast:
        return None

    temp = current.temp_f if UNITS == "imperial" else current.temp_c
    description = current.weather

    today_forecast = forecast.forecastday[0]
    high = today_forecast.high_f if UNITS == "imperial" else today_forecast.high_c
    low = today_forecast.low_f if UNITS == "imperial" else today_forecast.low_c

    return temp, description, high, low

# Build message
def build_message():
    now = datetime.datetime.now()
    hour = now.hour
    time_str = now.strftime("%I:%M %p")
    greeting = "Good morning" if hour < 12 else "Good evening"

    weather = get_weather(ZIP_CODE)
    if not weather:
        return f"{greeting}, this is {CALLSIGN}. The time is {time_str}. Weather data is currently unavailable."

    temp, description, high, low = weather
    if hour < 12:
        weather_msg = f"The current temperature is {int(temp)} degrees with {description}. Today's high is {int(high)} and the low is {int(low)}."
    else:
        weather_msg = f"The current temperature is {int(temp)} degrees with {description}."

    return f"{greeting}, this is {CALLSIGN}. The time is {time_str}. {weather_msg}"

# Run it
if __name__ == "__main__":
    message = build_message()
    print("Speaking:", message)
    speak(message)