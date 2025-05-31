import os
import speech_recognition as sr
from dotenv import load_dotenv
import threading
from colorama import Fore, init

# Load environment variables
load_dotenv()
AI_NAME = os.getenv("Assistantname")
USER = os.getenv("Username")

if not AI_NAME or not USER:
    raise ValueError("Required environment variables are not set.")

# Initialize colorama
init(autoreset=True)

class FastSpeechRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self._setup_recognizer()
        self.running = True

    def _setup_recognizer(self):
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 300
        self.recognizer.pause_threshold = 0.5
        self.recognizer.non_speaking_duration = 0.2

    def _print_user_input(self, text):
        print(f"\r{Fore.BLUE}{USER}: {Fore.CYAN}{text}")

    def listen_command(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            print(f"{Fore.GREEN}Listening...", end="", flush=True)
            
            try:
                audio = self.recognizer.listen(source, timeout=5)
                print(f"\r{Fore.LIGHTBLACK_EX}Recognizing...", end="", flush=True)
                
                recognized_text = self.recognizer.recognize_google(audio, language='en-IN').lower()
                self._print_user_input(recognized_text)
                return recognized_text

            except sr.UnknownValueError:
                print("\r" + Fore.RED + "Could not understand audio.")
                return ""
            except sr.RequestError as e:
                print(f"\r{Fore.RED}Recognition error: {e}")
                return ""
            except sr.WaitTimeoutError:
                print("\r" + Fore.RED + "Listening timed out while waiting for phrase to start.")
                return ""
            finally:
                print("\r", end="", flush=True)
                # os.system("cls" if os.name == "nt" else "clear")

    def continuous_listen(self, wake_word, callback):
        while self.running:
            command = self.listen_command()
            if command and wake_word.lower() in command:
                callback()

def speech_to_text():
    recognizer = FastSpeechRecognizer()
    # recognizer.continuous_listen(AI_NAME, lambda: print("Command recognized"))
    return recognizer.listen_command()



# def main():
#     recognizer = FastSpeechRecognizer()
#     try:
#         recognizer_thread = threading.Thread(
#             target=recognizer.continuous_listen, 
#             args=(AI_NAME.lower(), lambda: print("Command recognized"))
#         )
#         recognizer_thread.start()
#         recognizer_thread.join()
#     except KeyboardInterrupt:
#         recognizer.running = False
#         print("\nExiting...")

# if __name__ == "__main__":
#     main()