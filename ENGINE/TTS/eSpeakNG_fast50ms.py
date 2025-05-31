# from random import sample
import subprocess
import threading

from pyautogui import KEYBOARD_KEYS
# from torch import P
# from torch import T
import pygame
import os
import speech_recognition as sr
import time
# from pynput import keyboard
# PYNPUT_AVAILABLE = True

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    print("pynput library not found")
    PYNPUT_AVAILABLE = False

# brew install espeak-ng

def listen_for_interruption(stop_event, wake_words=None, threshold=600, sample_rate=16000):
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

def listen_for_keyboard_interruption(stop_event):
    """Listens specifically for the 's' key press and sets the stop_event."""
    if not PYNPUT_AVAILABLE:
        return # Do nothing if pynput is not installed

    def on_press(key):
        """Callback function when a key is pressed."""
        try:
            # Check if the pressed key's character is 's' (case-insensitive)
            if key.char.lower() == 's':
                print("\n[INFO] Keyboard interruption ('s' key) detected.")
                stop_event.set()
                # Stop the listener itself after the 's' key press
                return False
        except AttributeError:
            # This happens if a special key (like Shift, Ctrl, etc.) is pressed
            # We ignore special keys in this case
            pass

    # Create and start the listener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    # Keep the function alive until the listener stops (or main thread signals)
    # We also need a way for this thread to terminate if stop_event is set externally
    # (e.g., by voice command or when speech finishes normally)
    while listener.is_alive() and not stop_event.is_set():
        time.sleep(0.1) # Check periodically without busy-waiting

        # Ensure the listener is stopped if the loop exits because stop_event was set
        if listener.is_alive():
            listener.stop()
            break
        
    # print("[DEBUG] Keyboard listener stopped.") # Optional debug

def speak(text, rate=150, volume=100 , voice="Alex"):
    """
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
        "say",                # Command to run say on macOS
        # "espeak-ng",          # Command to run eSpeakNG
        "-o", temp_file,       # Output file name
        "--data-format=LEF32@32000",  # Data format
        # "-w","output.wav",        # Output file name
        # "-q",                  # Quiet mode: reduce console output
        # "-s", str(rate),       # Speech rate
        "-a", str(volume),     # Amplitude (volume)
        # "-p", "50",             # Pitch (0 to 200)
        # "-f", "output.wav",     # Output file name
        # "--punct=",            # Disable punctuation processing (if supported)
        "-r", str(rate),       # Speech rate
        "-v", voice,
        text
    ]
    subprocess.call(command)

    # Generate confirmation sound
    subprocess.call(["say", "-o", confirm_file, "--data-format=LEF32@32000", "-v", voice, "Okay, stopping now."])

    stop_event = threading.Event()
    listener_thread = threading.Thread(target=listen_for_interruption or listen_for_keyboard_interruption, args=(stop_event,), daemon=True)
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
        pygame.time.Clock().tick(30)

    pygame.mixer.quit()
    os.remove(temp_file)
    if os.path.exists(confirm_file):
        os.remove(confirm_file)

# if __name__ == "__main__":
# #     # Example input text that should be spoken exactly as provided.
# #     sample_text = "Jesa text aaya, AI se waisa hi bolna chahiye.Uses eSpeakNG to synthesize speech with minimal text normalization.Adjust options to reduce any text preprocessing, ensuring the output speech matches the input text.TTS systems are exploring these low latency targets. This code provides a conceptual framework that you can refine based on your actual model and deployment requirements. This is a test of a free, low-latency text-to-speech system. Achieving sub‑50ms latency end‑to‑end will depend on model efficiency, inference hardware (using GPUs can help), and the optimization of your phonemization and audio synthesis pipeline. In research, models like SyncSpeech and other dual‑stream TTS systems are exploring these low latency targets. This code provides a conceptual framework that you can refine based on your actual model and deployment requirements. This is a test of a free, low-latency text-to-speech system. Achieving sub‑50ms latency end‑to‑end will depend on model efficiency, inference hardware (using GPUs can help), and the optimization of your phonemization and audio synthesis pipeline. In research, models like SyncSpeech and other dual‑stream TTS systems are exploring these low latency targets. This code provides a conceptual framework that you can refine based on your actual model and deployment requirements."
#     sample_text = "This is a test of eSpeakNG text-to-speech synthesis. mene kya kiya"
#     speak(sample_text)

