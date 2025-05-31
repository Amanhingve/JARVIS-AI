# Automation/check_battery_persentage.py
import os
import sys
import psutil

# Get the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the project root to sys.path
sys.path.insert(0, project_root)



# from ENGINE.TTS.TTS_DF import speak
from ENGINE.TTS.eSpeakNG_fast50ms import speak


def battey_persentage():
    battery = psutil.sensors_battery()
    percent = int(battery.percent)
    speak(f"the device is running on {percent}% battery power")

    if percent < 30:
        speak("please connect the charger")
    elif percent > 80:
        speak("please disconnect the charger")
    else:
        speak("battery is in good condition")
        return percent

    return percent  # return the battery percentage

    # speak(f"the device is running on {percent}% battery power")
    
def get_battery_percentage_advice(): # Renamed and modified
    """Checks the battery percentage and returns advice as a string."""
    battery = psutil.sensors_battery()
    if battery is None:
        return "Sorry, I couldn't detect a battery."

    percent = int(battery.percent)
    result_message = f"The device is running on {percent}% battery power. " # Start building the message

    if percent < 30:
        result_message += "Please connect the charger."
    elif percent > 80:
        # Changed advice slightly - "disconnect" might be too strong unless fully charged.
        # You can adjust this threshold or message as needed.
        result_message += "The battery level is quite high."
    else:
        result_message += "The battery is in good condition."

    return result_message # Return the combined message


# if __name__ == "__main__":
#     battey_persentage()