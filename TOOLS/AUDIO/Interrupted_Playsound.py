import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame
import threading
import time

try: from TOOLS.AUDIO.Hotword_Detection import HotwordDetector
except ModuleNotFoundError: from Hotword_Detection import HotwordDetector
except: raise Exception("Failed to import Hotword_Detection module.")

def play_audio_Event(file_path: str, stop_event: threading.Event, prints: bool = False) -> None:
    """
    Plays an audio file. Stops playback if the stop_event is set.
    
    Args:
        file_path (str): The path to the audio file.
        stop_event (threading.Event): Event to signal stopping the playback.
        prints (bool): If True, enables print statements. Defaults to False.
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Error: Audio file not found: {file_path}")
            return
            
        # Initialize pygame mixer
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        
        # Try to load and play the file
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Wait for the audio to finish or for the stop event
            while pygame.mixer.music.get_busy() and not stop_event.is_set():
                time.sleep(0.1)
                
            # Stop the music if the stop event was set
            if stop_event.is_set():
                pygame.mixer.music.stop()
                
        except pygame.error as e:
            print(f"Error playing audio file: {e}")
            print(f"Try converting {file_path} to WAV format with: ffmpeg -i {file_path} -acodec pcm_s16le output.wav")
            
    except Exception as e:
        print(f"Unexpected error in play_audio_Event: {e}")
    finally:
        # Clean up pygame mixer
        try:
            pygame.mixer.quit()
        except:
            pass

def detect_hotword(detector: HotwordDetector, stop_event: threading.Event, prints: bool = False) -> None:
    """
    Detects hotwords using the HotwordDetector instance. Sets the stop_event if a hotword is detected.
    
    Args:
        detector (HotwordDetector): The hotword detector instance.
        stop_event (threading.Event): Event to signal that a hotword has been detected.
        prints (bool): If True, enables print statements. Defaults to False.
    """
    hotword_detected = detector.listen_for_hotwords()
    if hotword_detected:
        stop_event.set()
        if prints: print("Hotword detected, Setting Stop Event.")

def play_audio(audio_file_path: str, prints: bool = False, stop_event: threading.Event = None) -> None:
    """
    play_audio function to run audio playback and hotword detection concurrently.
    
    Args:
        audio_file_path (str): The path to the audio file.
        prints (bool): If True, enables print statements. Defaults to False.
    """
    if stop_event is None:
        stop_event = threading.Event()
    # stop_event = threading.Event()
    detector = HotwordDetector()

    audio_thread = threading.Thread(target=play_audio_Event, args=(audio_file_path, stop_event, prints))
    hotword_thread = threading.Thread(target=detect_hotword, args=(detector, stop_event, prints))

    audio_thread.start()
    hotword_thread.start()

    audio_thread.join()
    # detector.stop()
    hotword_thread.join()

    if prints: print("Application exited gracefully.")

# if __name__ == "__main__":
#     audio_file_path = 'ASSETS/output_audio.mp3'  # Replace with the path to your audio file
#     play_audio(audio_file_path)