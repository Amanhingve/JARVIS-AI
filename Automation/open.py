import time

import pyautogui as ui
from Data.DLG import open_dld
import random

from ENGINE.TTS.eSpeakNG_fast50ms import speak


def open(text):
    x = random.choice(open_dld)
    speak(x+""+text)
    time.sleep(0.5)
    ui.hotkey("win")
    time.sleep(0.2)
    ui.write(text)
    time.sleep(0.5)
    ui.press("enter")

