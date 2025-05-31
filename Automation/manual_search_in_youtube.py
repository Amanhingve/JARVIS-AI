import pyautogui as ui
import random
import time
from DATA.DLG import s2, s1
from FUNCTION.speak import speak


def search_manual(text):
    text = text .replace("search","")
    ui.press("/")
    ui.write(text)
    s12 = random.choice(s1)
    speak( s12 )
    time.sleep(0.5)
    ui.press("enter")
    s12 = random.choice(s2)
    speak(s12)

