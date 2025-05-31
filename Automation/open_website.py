import difflib
import random
import webbrowser
from Data.DLG import websites, open_dld, success_open, open_maybe, sorry_open
from ENGINE.TTS.eSpeakNG_fast50ms import speak


def openweb(text):

    # Convert the input to lowercase for case-insensitive matching
    website_name_lower = text.lower()

    # Check if the exact website name exists in the dictionary
    if website_name_lower in websites:
        random_dlg = random.choice(open_dld)
        speak(random_dlg + text)
        url = websites[website_name_lower]
        webbrowser.open(url)
        randonsuccess = random.choice(success_open)
        speak(randonsuccess)
    else:
        # Find the closest matching website using string similarity
        matches = difflib.get_close_matches(website_name_lower, websites.keys(), n=1, cutoff=0.6)
        if matches:
            random_dlg = random.choice(open_dld)
            randonopen2 = random.choice(open_maybe)
            closest_match = matches[0]
            speak(randonopen2 + random_dlg + text)
            url = websites[closest_match]
            webbrowser.open(url)
            randonsuccess = random.choice(success_open)
            speak(randonsuccess)
        else:
            randonsorry = random.choice(sorry_open)
            speak(randonsorry +" named " + text)


