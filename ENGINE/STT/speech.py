# /ENGINE/STT/speech.py
import os
import speech_recognition as sr
from dotenv import load_dotenv
# from mtranslate import translate
from colorama import Fore, Style, init

"""
Project: Speech-to-Text with Translation
Description: A Python script that listens to user input, converts speech to text, and translates it in real-time.
"""

load_dotenv()
init(autoreset=True)

class SpeechToTextListener:
    """A class for performing speech-to-text and translating the recognized text."""

    def __init__(self, language: str = "en"):
        """Initializes the SpeechToTextListener class."""
        global noise_level # Global variable for noise level
        self.language = language
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True  # Enable dynamic adjustment for varying audio levels
        noise_level = self.recognizer.energy_threshold =44000 # Set a moderate energy threshold to filter out background noise
        self.recognizer.dynamic_energy_adjustment_damping = 0.15  # Slower adjustment to avoid sudden changes
        self.recognizer.dynamic_energy_ratio = 2.0  # Higher ratio for better sensitivity to speech
        self.recognizer.pause_threshold = 0.8  # Time to wait after speech ends
        self.recognizer.operation_timeout = None
        self.recognizer.phrase_threshold = 0.3  # Minimum length of a phrase to consider
        self.recognizer.non_speaking_duration = 0.2  # Duration of non-speaking audio to ignore
        self.user = os.getenv("USER", "User")
        NOISE_THRESHOLD = 800
        if noise_level > NOISE_THRESHOLD:
                print("Too much background noise, skipping recognition.")
                return None  # Ignore input when it's too noisy
    

    def stream(self, content: str):
        """Prints the given content to the console with formatting."""
        print(Fore.BLUE + f"{self.user} : " + Fore.CYAN + f"{content}")

    def listen(self) -> str:
        """Listens to the microphone and performs speech-to-text."""
        with sr.Microphone() as source:
            # Adjust for ambient noise to filter out background sounds
            self.recognizer.adjust_for_ambient_noise(source, duration=4)  # Increase duration for better noise calibration
            # self.recognizer.energy_threshold = max(3000, self.recognizer.energy_threshold)  # Dynamically adjust energy threshold
            self.recognizer.energy_threshold = max(400, noise_level)  # Higher threshold for noise
            print(Fore.GREEN + "Listening...", end="", flush=True)
            try:
                # Listen to the microphone with a timeout
                audio = self.recognizer.listen(source, timeout=5)  # Stop listening after 5 seconds of silence

                print("\r" + Fore.LIGHTBLACK_EX + "Recognizing...", end="", flush=True)
                # Recognize speech using Google's Speech Recognition API
                recognized_text = self.recognizer.recognize_google(audio).lower()
                print("\r" + Fore.GREEN + f"Recognized: {recognized_text}")
                return recognized_text
            except sr.UnknownValueError:
                print(Fore.RED + "Could not understand audio (no speech detected).")
                return ""
            except sr.RequestError as e:
                print(Fore.RED + f"Request error: {e}")
                return ""
            except sr.WaitTimeoutError:
                print(Fore.RED + "Listening timed out (no speech detected).")
                return ""

    def main(self):
        """Main function to continuously listen and translate speech."""
        while True:
            recognized_text = self.listen()
            if recognized_text:
                # translated_text = self.translate_text(recognized_text, self.language)
                self.stream(recognized_text)

def speech_to_text():
    listener = SpeechToTextListener(language="en")
    listener.main()


# class SpeechProcessor:
#     def __init__(self, source):
#         self.recognizer = sr.Recognizer()
#         self.microphone = source
#         self.ai_name = AI_NAME.lower()
#         self.ai_name_upper = AI_NAME.upper()
#         self.ai_name_title = AI_NAME.title()
#         self.ai_name_capitalize = AI_NAME.capitalize()
#         self.ai_name_length = len(AI_NAME)
#         self.ai_name_words = AI_NAME.split(" ")
#         self.ai_name_chars = list(AI_NAME)
#         self.ai_name_first_char = AI_NAME[0]
#         self.ai_name_last_char = AI_NAME[-1]
#         self.ai_name_vowels = [char for char in self.ai_name_chars if char in "aeiou"]
#         self.ai_name_consonants = [char for char in self.ai_name_chars if char not in "aeiou"]
#         self.ai_name_vowel_count = len(self.ai_name_vowels)
#         self.ai_name_consonant_count = len(self.ai_name_consonants)
#         self.ai_name_vowel_percentage = self.ai_name_vowel_count / self.ai_name_length
#         self.ai_name_consonant_percentage = self.ai_name_consonant_count / self.ai_name_length
#         self.ai_name_vowels_str = "".join(self.ai_name_vowels)
#         self.ai_name_consonants_str = "".join(self.ai_name_consonants)
#         self.ai_name_vowels_count_str = str(self.ai_name_vowel_count)
#         self.ai_name_consonants_count_str = str(self.ai_name_consonant_count)
#         self.ai_name_vowel_percentage_str = str(self.ai_name_vowel_percentage)
#         self.ai_name_consonant_percentage_str = str(self.ai_name_consonant_percentage)        

#         self.engine = pyttsx3.init()
#         self.engine.setProperty('rate', 150)
#         self.engine.setProperty('volume', 1.0)

#         self.recognizer = sr.Recognizer()
#         self.microphone = sr.Microphone(device_index=1)

#         self.translations = {
#             "en": "English",
#             "en-IN": "English (India)",
#             "hi": "Hindi",
#             "bn": "Bengali",
#             "pa": "Punjabi",
#             "te": "Telugu",
#             "mr": "Marathi",
#             "ta": "Tamil",
#             "ur": "Urdu",
#             "gu": "Gujarati",
#             "kn": "Kannada",
#             "ml": "Malayalam",
#         }


#     def speak(self, text):
#         self.engine.say(text)
#         self.engine.runAndWait()

#     def listen(self):
#         with self.microphone as source:
#             self.recognizer.adjust_for_ambient_noise(source)
#             audio = self.recognizer.listen(source)
#         try:
#             return self.recognizer.recognize_google(audio)
#         except sr.UnknownValueError:
#             return None
#         except sr.RequestError:
#             return None

#     def listen_command(self):
#         command = self.listen()
#         if command:
#             return command.lower()
#         else:
#             return None 

#     def continuous_listen(self, wake_word, callback):
#         while True:
#             command = self.listen()
#             if command and wake_word in command:
#                 callback()
#             else:
#                 pass

#     def recognize_and_respond(self, wake_word, response):
#         def callback():
#             self.speak(response)
#         self.continuous_listen(wake_word, callback)

#     def translate_text(self, text, target_language):
#         translation = translate(text, target_language)
#         return translation

#     def translate_and_speak(self, text, target_language):
#         translated_text = self.translate_text(text, target_language)
#         self.speak(translated_text)
#         return translated_text

#     def get_supported_languages(self):
#         return self.translations

#     def get_supported_languages_str(self):
#         return ", ".join(self.translations.values())

#     def get_supported_languages_code(self):
#         return self.translations.keys()

#     def get_supported_languages_code_str(self):
#         return ", ".join(self.translations.keys())

#     def get_supported_languages_info(self):
#         return self.translations.items()

#     def get_supported_languages_info_str(self):
#         return "\n".join([f"{code}: {language}" for code, language in self.translations.items()])

#     def get_supported_languages_info_code(self):
#         return self.translations.items()

#     def get_supported_languages_info_code_str(self):
#         return "\n".join([f"{code}: {language}" for code, language in self.translations.items()])
        


# if __name__ == "__main__":
#     processor = SpeechProcessor()
#     processor.continuous_listen("hello", processor.speak)




