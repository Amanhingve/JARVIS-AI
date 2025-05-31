import os
import subprocess
import tempfile
import threading
from playsound import playsound  # pip install playsound
import edge_tts
import asyncio

async def synthesize_text_to_file(text: str, voice: str, output_file: str) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def speak(text: str, voice: str = 'en-CA-LiamNeural') -> None:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_mp3_file:
            temp_mp3_filename = temp_mp3_file.name

        asyncio.run(synthesize_text_to_file(text, voice, temp_mp3_filename))
        playsound(temp_mp3_filename)
        os.remove(temp_mp3_filename)
        
    except Exception as e:
        print(f"Error: {e}")

# while True:
    # input_text = input("Enter text: ")
    # speak(input_text)
speak("Hello, my name is Jarvis")