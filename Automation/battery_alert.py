import random
import time
import psutil
from Data.DLG import low_b, last_low, full_battery
from ENGINE.TTS.eSpeakNG_fast50ms import speak


def battery_alert():
    while True:
        time.sleep(10)
        battery = psutil.sensors_battery()
        percent = int(battery.percent)

        if percent < 10:
            random_low = random.choice(last_low)
            speak(random_low)

        elif percent < 30:
            random_low = random.choice(low_b)
            speak(random_low)

        elif percent == 100:
            random_low = random.choice(full_battery)
            speak(random_low)
        else:
            pass

        time.sleep(1500)

def battery_alert1():
    """Checks the current battery status once and returns a descriptive string."""
    battery = psutil.sensors_battery()
    if battery is None:
        return "Sorry, I couldn't detect a battery."
        
    percent = int(battery.percent)
    is_plugged = battery.power_plugged
    status_message = f"Battery is at {percent}%."

    if is_plugged:
        status_message += " (Plugged in / Charging)"
    else:
        status_message += " (Discharging)"

    message = ""
    if percent < 10:
        message = random.choice(last_low)
    elif percent < 30:
        message = random.choice(low_b)
    elif percent == 100:
        message = random.choice(full_battery)
    else:
        # Provide a specific message for good levels instead of just the percentage
        message = f"Sir, your battery level is {percent}%, which is perfectly fine."

    # Combine the specific message with the status details
    return f"{message} ({status_message})"
    