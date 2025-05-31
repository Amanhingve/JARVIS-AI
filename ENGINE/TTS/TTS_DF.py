import asyncio
import threading
import os
import edge_tts
import pygame
import time

# Voice = "en-US-GuyNeural"
# hi-IN-MadhurNeural - hi-IN (Male)
# en-IN-NeerjaNeural - en-IN (Female)
Voice = "hi-IN-MadhurNeural"
BUFFER_SIZE = 1024
SPEECH_RATE = 40
PITCH = 0
AUDIO_DIR = "ASSETS/audio"  # Define a constant for the audio directory


def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def remove_file(file_path):
    max_attempts = 3
    attempts = 0
    while attempts < max_attempts:
        try:
            os.remove(file_path)
            break
        except OSError as e:
            print(f"Error removing file {file_path}: {e}")
            attempts += 1
            time.sleep(0.1)  # Wait a bit before retrying
    if attempts == max_attempts:
        print(f"Failed to remove file {file_path} after multiple attempts.")


async def synthesize_text_to_file(text, output_file, speech_rate=SPEECH_RATE, pitch=PITCH):
    try:
        cm_text = edge_tts.Communicate(text, Voice, rate=f"+{speech_rate}%", pitch=f"+{pitch}Hz")
        await cm_text.save(output_file)
    except Exception as e:
        print(f"Error during text synthesis: {e}")
        raise


def play_audio(file_path, event):
    try:
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy() and not event.is_set():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.stop()
        pygame.mixer.quit()
    except Exception as e:
        print(f"Error during audio playback: {e}")
    finally:
        remove_file(file_path)


def speak(text, output_file=None, speech_rate=SPEECH_RATE, pitch=PITCH):
    """
    Synthesizes text to speech and plays it, aiming for low latency.

    Args:
        text (str): The text to speak.
        output_file (str, optional): The path to save the audio file. Defaults to a temporary file in ASSETS/audio.
        speech_rate (int, optional): The speech rate adjustment. Defaults to SPEECH_RATE.
        pitch (int, optional): The pitch adjustment. Defaults to PITCH.
    """
    try:
        if output_file is None:
            ensure_directory_exists(AUDIO_DIR)
            output_file = os.path.join(AUDIO_DIR, "temp_speech.mp3")

        ensure_directory_exists(os.path.dirname(output_file))

        # Create a threading event to control playback
        stop_event = threading.Event()

        # Synthesize text to file in a separate thread
        synthesis_thread = threading.Thread(
            target=asyncio.run,
            args=(synthesize_text_to_file(text, output_file, speech_rate, pitch),),
        )
        synthesis_thread.start()

        # Wait for synthesis to complete before starting playback
        synthesis_thread.join()

        # Play audio in a separate thread
        playback_thread = threading.Thread(target=play_audio, args=(output_file, stop_event))
        playback_thread.start()

        # Wait for a short time to simulate 50ms latency
        time.sleep(0.05)

        # If you want to stop the playback prematurely, you can set the event:
        # stop_event.set()

        # Wait for the playback thread to finish
        playback_thread.join()

    except Exception as e:
        print(f"Error in speak function: {e}")


# Example usage:
if __name__ == "__main__":
    speak("my name is Jarvis")
    speak("Hello, how are you?")
    speak("I am fine, thank you.")
    speak("What is your name?")
    speak("aman ji, main aapke bare mein itna janta hoon ki aapka naam aman hai, aur aapne mujhe create kiya hai. Iske alawa main aapke bare mein kuchh nahin janta.")
    speak("Take your content creation to the next level with our cutting-edge Text-to-Video Converter!")
