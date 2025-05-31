# import os
# from groq import Groq
# from dotenv import dotenv_values

# # Load environment variables from .env file
# env_vars = dotenv_values(".env")

# # Access environment variables
# GroqAPIKey = env_vars.get("GroqAPIKey")

# # Initialize Groq client
# client = Groq(api_key=GroqAPIKey)


# # Specify the path to the audio file
# filename = os.path.dirname(__file__) + "/ASSETS/audio/audio_file.mp3" # Replace with your audio file!

# # Open the audio file
# with open(filename, "rb") as file:
#     # Create a transcription of the audio file
#     transcription = client.audio.transcriptions.create(
#       file=(filename, file.read()), # Required audio file
#       model="whisper-large-v3-turbo", # Required model to use for transcription
#       prompt="Specify context or spelling",  # Optional
#       language="en", # Optional
#       response_format="json",  # Optional
#     #   language="en",  # Optional
#       temperature=0.0  # Optional
#     )
#     # Print the transcription text
#     print(transcription.text)

# import pvporcupine
# import pyaudio
# from pyaudio import paInputOverflowed
# import struct
# import time
# import os
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# # Access environment variables
# ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY")

# def hotword():
#     porcupine = None
#     paud = None
#     audio_stream = None
#     keywords = ["jarvis", "alexa"]  # Maintain a list of keywords
#     try:
#         print("Initializing Porcupine...")
#         porcupine = pvporcupine.create(access_key=ACCESS_KEY, keywords=keywords)
#         print("Porcupine initialized.")

#         paud = pyaudio.PyAudio()
#         print("PyAudio initialized.")

#         audio_stream = paud.open(
#             rate=porcupine.sample_rate,
#             channels=1,
#             format=pyaudio.paInt16,
#             input=True,
#             frames_per_buffer=porcupine.frame_length * 2
#         )
#         print("Audio stream opened.")
        
#         print("Listening for hotwords...")
#         while True:
#             try:
#               keyword = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
#               keyword = struct.unpack_from("h" * porcupine.frame_length, keyword)

#               keyword_index = porcupine.process(keyword)
#               if keyword_index >= 0:
#                   print(f"Hotword detected: {keywords[keyword_index]}")  # Use the keywords list

#                   # Simulate Command+J shortcut
#                   import pyautogui as autogui
#                   autogui.keyDown("command")
#                   autogui.press("j")
#                   autogui.keyUp("command")
#                   time.sleep(0.5)
#             except paInputOverflowed:
#               print("Warning: Audio input overflowed. Skipping this frame.")
#     except pvporcupine.PorcupineInvalidArgumentError as e:
#         print(f"Error: Invalid AccessKey or keyword. Please check your AccessKey and keywords. {e}")
#     except Exception as e:
#         print(f"An error occurred: {e}")
#     finally:
#         if porcupine is not None:
#             porcupine.delete()
#         if audio_stream is not None:
#             audio_stream.close()
#         if paud is not None:
#             paud.terminate()

# if __name__ == "__main__":
#     hotword()

# import time
# from RealtimeTTS import TextToAudioStream, SystemEngine
# # import logging

# # Configure logging to show warnings and errors
# # logging.basicConfig(level=logging.WARNING)

# # Patch the SystemEngine to avoid the "run loop not started" error
# class PatchedSystemEngine(SystemEngine):
#     def __init__(self):
#         super().__init__()
#         self.is_running = False

#     def synthesize(self, sentence):
#         try:
#             print(f"Synthesizing sentence: {sentence}")
#             if not self.is_running:
#                 self.engine.startLoop(0)
#                 self.is_running = True
#             self.engine.say(sentence)
#             self.engine.runAndWait()  # Use runAndWait to ensure the loop starts
#             print("Synthesis complete")
#             return True
#         except Exception as e:
#             print(f"Error synthesizing sentence: {e}")
#             return False
    
#     def stop(self):
#         if self.is_running:
#             self.engine.endLoop()
#             self.is_running = False

# # Use the patched engine
# engine = PatchedSystemEngine()
# stream = TextToAudioStream(engine)

# try:
#     # Feed the text you want to convert
#     stream.feed("Hello! This is a test of a free,")
#     stream.feed("low-latency text-to-speech system.")

#     # Start playback asynchronously
#     stream.play_async()

#     # Wait until playback finishes
#     while stream.is_playing():
#         time.sleep(0.1)
# except KeyboardInterrupt:
#     print("Program interrupted by user.")
# finally:
#     engine.stop()
#     print("Program exited.")

# import subprocess

# def speak_with_espeak(text, rate=150, volume=100):
#     """
#     Convert text to speech using eSpeakNG with low latency.
#     :param text: The text string to speak.
#     :param rate: The speed of speech (default 150 words per minute).
#     :param volume: The volume level (0 to 200, default 100).
#     """
#     # Construct the command. '-s' sets speed; '-a' sets amplitude/volume.
#     command = [
#         "espeak-ng",            # Command for eSpeakNG
#         "-s", str(rate),        # Speed of speech (words per minute)
#         "-a", str(volume),      # Amplitude (volume level)
#         text                    # The text to be spoken
#     ]
#     # Call eSpeakNG, which plays the speech immediately (low latency)
#     subprocess.call(command)

# if __name__ == "__main__":
#     sample_text = "Hello, this is a fast text to speech synthesis test with low latency."
#     speak_with_espeak(sample_text)

# from gtts import gTTS
# import os

# def speak_with_gtts(text, lang="en"):
#     """
#     Convert text to speech using Google TTS (gTTS).
#     :param text: The text string to speak.
#     :param lang: The language code (default is 'en' for English).
#     """
#     tts = gTTS(text=text, lang=lang, slow=False, tld="com.au")  # Removed 'stream' argument
#     tts.save("output.mp3")
#     os.system("afplay output.mp3")  # Use 'afplay' on macOS to play the audio

# if __name__ == "__main__":
#     sample_text = (
#         "Hello, this is a fast text-to-speech synthesis test with low latency. "
#         "This is a test of a free, low-latency text-to-speech system. "
#         "Achieving sub‑50ms latency end‑to‑end will depend on model efficiency, "
#         "inference hardware (using GPUs can help), and the optimization of your phonemization "
#         "and audio synthesis pipeline. In research, models like SyncSpeech and other dual‑stream "
#         "TTS systems are exploring these low latency targets. This code provides a conceptual framework "
#         "that you can refine based on your actual model and deployment requirements."
#     )
#     speak_with_gtts(sample_text)

# 
import subprocess
import threading
import pygame
import os
import speech_recognition as sr


def listen_for_interruption(stop_event, wake_words=None, threshold=0.6):
    if wake_words is None:
        wake_words = ["stop jarvis", "pause", "stop now", "stop", "pause now", "pause jarvis"]
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
    while not stop_event.is_set():
        try:
            with mic as source:
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
                spoken = recognizer.recognize_google(audio, show_all=True)
                if isinstance(spoken, dict) and "alternative" in spoken:
                    for alt in spoken["alternative"]:
                        transcript = alt.get("transcript", "").lower()
                        confidence = alt.get("confidence", 1.0)
                        # print(f"[DEBUG] Heard: '{transcript}' with confidence {confidence:.2f}")
                        if any(wake_word in transcript for wake_word in wake_words) and confidence >= threshold:
                            stop_event.set()
                            break
        # except Exception as e:
        #     print(f"[DEBUG] Recognition error: {e}")
        except:
            pass  # timeout or recognition error; do nothing


def speak(text, rate=150, volume=100 , voice="Alex"):
    """
    Uses macOS 'say' to synthesize speech and plays it with interruption if wake words (e.g. 'stop jarvis', 'pause') are detected.
    Uses eSpeakNG to synthesize speech with minimal text normalization.
    Adjust options to reduce any text preprocessing, ensuring the output speech matches the input text.
    
    Parameters:
      text (str): Input text to be spoken.
      rate (int): Speed of speech (words per minute).
      volume (int): Volume level (0 to 200).
      voice (str): Voice selection. exmple :- "Alex", "Daniel", "Microsoft Zira Desktop", "Samantha", "Tony",
      indian voices (str): "Rishi", "Lekha", "Veena",en-in
      gana voice (str): "Good News", Cellos
      macOS voice check : say -v "?" .   
      windows voice check : powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }"
      linux voice check : espeak-ng --voices .
    """
    # The "--punct=" flag can help disable punctuation normalization
    # Check your eSpeakNG documentation as options may vary by version.
    

    temp_file = "temp.wav"
    confirm_file = "confirm.wav"
    # stop_event = threading.Event()

    # Generate speech audio using macOS `say`
    command = [
        "say", "-o", temp_file,
        "--data-format=LEF32@32000",
        "-a", str(volume),
        "-r", str(rate),
        "-v", voice,
        text
    ]
    subprocess.call(command)

    # Generate confirmation sound
    subprocess.call(["say", "-o", confirm_file, "--data-format=LEF32@32000", "-v", voice, "Okay, stopping now."])

    stop_event = threading.Event()
    listener_thread = threading.Thread(target=listen_for_interruption, args=(stop_event,), daemon=True)
    listener_thread.start()

    # Play the audio
    pygame.mixer.init()
    pygame.mixer.music.load(temp_file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        if stop_event.is_set():
            pygame.mixer.music.stop()
            pygame.mixer.music.load(confirm_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            break
        pygame.time.Clock().tick(10)

    pygame.mixer.quit()
    os.remove(temp_file)
    if os.path.exists(confirm_file):
        os.remove(confirm_file)

if __name__ == "__main__":
#     # Example input text that should be spoken exactly as provided.
    sample_text = "Jesa text aaya, AI se waisa hi bolna chahiye.Uses eSpeakNG to synthesize speech with minimal text normalization.Adjust options to reduce any text preprocessing, ensuring the output speech matches the input text.TTS systems are exploring these low latency targets. This code provides a conceptual framework that you can refine based on your actual model and deployment requirements. This is a test of a free, low-latency text-to-speech system. Achieving sub‑50ms latency end‑to‑end will depend on model efficiency, inference hardware (using GPUs can help), and the optimization of your phonemization and audio synthesis pipeline. In research, models like SyncSpeech and other dual‑stream TTS systems are exploring these low latency targets. This code provides a conceptual framework that you can refine based on your actual model and deployment requirements. This is a test of a free, low-latency text-to-speech system. Achieving sub‑50ms latency end‑to‑end will depend on model efficiency, inference hardware (using GPUs can help), and the optimization of your phonemization and audio synthesis pipeline. In research, models like SyncSpeech and other dual‑stream TTS systems are exploring these low latency targets. This code provides a conceptual framework that you can refine based on your actual model and deployment requirements."
    # sample_text = "This is a test of eSpeakNG text-to-speech synthesis. mene kya kiya"
    speak(sample_text)

