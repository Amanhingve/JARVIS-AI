# Automation/search_in_google.py

import pywhatkit
import random
from Data.DLG import search_result
from ENGINE.TTS.eSpeakNG_fast50ms import speak
from ENGINE.STT.new_fast_stt import speech_to_text


def search_google(query: str) -> str:
    """ Searches the given query on Google and returns the first result. """
    speak("what do you want to search on google sir")
    speak("please tell me")
    text = speech_to_text().lower()
    dlg = random.choice(search_result)
    pywhatkit.search(text)
    speak(dlg)
