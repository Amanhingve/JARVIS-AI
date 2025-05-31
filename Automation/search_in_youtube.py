import random
import time
import pyautogui as ui
import webbrowser
from Data.DLG import yt_search, s1, s2
from ENGINE.TTS.eSpeakNG_fast50ms import speak


def youtube_search(text):
    dlg = random.choice(yt_search)
    speak(dlg)
    webbrowser.open("https://www.youtube.com/")
    time.sleep(2)
    ui.press("/")
    ui.write(text)
    s12 = random.choice(s1)
    speak( s12 )
    time.sleep(0.5)
    ui.press("enter")
    s12 = random.choice(s2)
    speak(s12)

# Example usage
# if __name__ == "__main__":
#     # Replace with the text you want to search for
#     search_text = "Python programming"
#     youtube_search(search_text)