import random
import pyautogui as ui
from Data.DLG import closedlg
from ENGINE.TTS.eSpeakNG_fast50ms import speak

closedlg_random = random.choice(closedlg)
def close():
    speak(closedlg_random)
    ui.hotkey("alt","f4")