from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import librosa
import soundfile as sf
import numpy as np
import os

"""
Project: Realtime Speech to Text Listener
Description: A Python script that uses Selenium to interact with a website and listen to user input & print them in real time.
"""

class SpeechToTextListener:
    """A class for performing speech-to-text using a web-based service."""

    def __init__(
            self, 
            website_path: str = "https://realtime-stt-devs-do-code.netlify.app/", 
            language: str = "en-in",
            wait_time: int = 10,
            min_voice_level: float = 0.01,  # Minimum voice level threshold
            max_voice_level: float = 0.3):  # Maximum voice level threshold
        
        """Initializes the STT class with the given website path and language."""
        self.website_path = website_path
        self.language = language
        self.min_voice_level = min_voice_level
        self.max_voice_level = max_voice_level
        self.chrome_options = Options()
        self.chrome_options.add_argument("--use-fake-ui-for-media-stream")
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
        self.chrome_options.add_argument("--headless=new")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.wait = WebDriverWait(self.driver, wait_time)

    def stream(self, content: str):
        """Prints the given content to the console with a yellow color, overwriting previous output, with "speaking..." added."""
        print("\033[96m\rUser Speaking: \033[93m" + f" {content}", end='', flush=True)

    def get_text(self) -> str:
        """Retrieves the transcribed text from the website."""
        return self.driver.find_element(By.ID, "convert_text").text

    def select_language(self):
        """Selects the language from the dropdown using JavaScript."""
        self.driver.execute_script(
            f"""
            var select = document.getElementById('language_select');
            select.value = '{self.language}';
            var event = new Event('change');
            select.dispatchEvent(event);
            """
        )

    def verify_language_selection(self):
        """Verifies if the language is correctly selected."""
        language_select = self.driver.find_element(By.ID, "language_select")
        selected_language = language_select.find_element(By.CSS_SELECTOR, "option:checked").get_attribute("value")
        return selected_language == self.language

    def main(self) -> Optional[str]:
        """Performs speech-to-text conversion and returns the transcribed text."""
        self.driver.get(self.website_path)
        
        # Ensure the dropdown options are fully loaded before selecting
        self.wait.until(EC.presence_of_element_located((By.ID, "language_select")))
        
        # Select the language using JavaScript
        self.select_language()

        # Verify the language selection
        if not self.verify_language_selection():
            print(f"Error: Failed to select the correct language. Selected: {self.verify_language_selection()}, Expected: {self.language}")
            return None

        self.driver.find_element(By.ID, "click_to_record").click()

        is_recording = self.wait.until(
            EC.presence_of_element_located((By.ID, "is_recording"))
        )

        print("\033[94m\rListening...", end='', flush=True)
        while is_recording.text.startswith("Recording: True"):
            text = self.get_text()
            if text:
                self.stream(text)
            is_recording = self.driver.find_element(By.ID, "is_recording")

        return self.get_text()

    def listen(self, prints: bool = False) -> Optional[str]:
        """Starts the listening process by navigating to the website, selecting the desired language, and
            initiating speech-to-text conversion. The function returns the transcribed text if the
            listening process completes successfully.
        """
        while True:
            result = self.main()
            if result and len(result) != 0:
                print("\r" + " " * (len(result) + 16) + "\r", end="", flush=True)
                if prints: print("\033[92m\rYOU SAID: " + f"{result}\033[0m\n")
                break
        return result

    def reduce_noise(self, audio_path: str, output_path: str):
        """Reduces background noise from the given audio file using librosa."""
        y, sr = librosa.load(audio_path, sr=None)
        # Perform noise reduction
        reduced_noise_audio = librosa.effects.split(y, top_db=20)
        cleaned_audio = np.concatenate([y[start:end] for start, end in reduced_noise_audio])
        sf.write(output_path, cleaned_audio, sr)

    def filter_voice_levels(self, audio_path: str, output_path: str):
        """Filters out audio segments below min_voice_level and above max_voice_level."""
        y, sr = librosa.load(audio_path, sr=None)
        S_full, phase = librosa.magphase(librosa.stft(y))

        # Create a mask to filter out segments
        mask = (S_full > self.min_voice_level) & (S_full < self.max_voice_level)
        filtered_audio = librosa.istft(mask * S_full * phase)

        sf.write(output_path, filtered_audio, sr)

def speech_to_text():
    listener = SpeechToTextListener(language="en-IN")  # You can specify the desired language here
    speech = listener.listen()
    return speech

# if __name__ == "__main__":
#     # listener = SpeechToTextListener(language="hi-IN")  # You can specify the desired language here
#     # speech = listener.listen()
#     # print("FINAL EXTRACTION: ", speech)
#     while True:
#         speech_to_text()