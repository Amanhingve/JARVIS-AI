import random
import psutil
import os
import sys
import warnings
import logging

# Hide warnings
warnings.filterwarnings('ignore')
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide" # Hide pygame welcome message
# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Hide TensorFlow warnings
# logging.getLogger('transformers').setLevel(logging.ERROR)
# Get the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the project root to sys.path
sys.path.insert(0, project_root)

from Data.DLG import plug_out, plug_in
from ENGINE.TTS.TTS_DF import speak


def check_plugin_status():
    battery = psutil.sensors_battery()
    previous_state = battery.power_plugged

    while True:
        battery = psutil.sensors_battery()

        if battery.power_plugged != previous_state:
            if battery.power_plugged:
              random_low = random.choice(plug_in)
              speak(random_low)
            else:
              random_low = random.choice(plug_out)
              speak(random_low)

            previous_state = battery.power_plugged

previous_state = None
plug_in1 = ["charger is plugged check conform", "battery is charging that means charger is plugged check completed"]
plug_out1 = ["Charger status unplugged", "battery is not charging that means charger is not plugged check completed"]
def check_plugin_status1():
    global previous_state  # Use the global variable

    battery = psutil.sensors_battery()

    if battery.power_plugged != previous_state:
        if battery.power_plugged:
            random_low = random.choice(plug_in1)
            speak(random_low)  # Assuming speak function is defined
        else:
            random_low = random.choice(plug_out1)
            speak(random_low)  # Assuming speak function is defined

        previous_state = battery.power_plugged       


# check_plugin_status1()  # Call the function to start the loop
# check_plugin_status()  # Call the function to start the loop
# if __name__ == "__main__":