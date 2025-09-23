# AllStar Time & Weather Announcer

This Python script speaks the current time, date, and weather conditions over your AllStar node using `asl-tts`. It pulls live data from the National Weather Service (NWS) and adapts its message based on time of day — including highs and lows in the morning, and humidity when relevant.

---

## Setup Instructions

### 1. Install Dependencies

Run this from your terminal:

```bash
pip install -r requirements.txt

```
### 2. Edit the Script

Open asl_day_time.py and update the configuration block at the top:

```bash
CALLSIGN = "K0IRO"                     # Your repeater's call sign
ZIP_CODE = "50208"                    # ZIP code for weather lookup
NODE_ID = 12345                       # Your AllStar node number
USER_AGENT_EMAIL = "your_email@example.com"  # Used for API header (required)
```

### 3. Example Output

Good afternoon, this is the K0IRO Repeater. Today is Tuesday September 23rd and time is 03:40 PM. The current temperature is 83 degrees with sunny skies. The humidity is 65 percent.

or

Good morning, this is the K0IRO Repeater. Today is Tuesday September 23rd and time is 08:15 AM. The current temperature is 63 degrees with cloudy skies. Today's high is 72 and the low is 58.

### 4. Schedule with CRON

To run this script automatically at 8:15 AM and 8:15 PM, add the following lines to your crontab:

```bash
15 8 * * * /usr/bin/python3 /full/path/to/asl_day_time.py
15 20 * * * /usr/bin/python3 /full/path/to/asl_day_time.py
```
