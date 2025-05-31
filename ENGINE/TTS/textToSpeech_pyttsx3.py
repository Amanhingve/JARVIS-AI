import pyttsx3 # pip install pyttsx3 # pyttsx3 is a text-to-speech conversion library in Python. Unlike alternative libraries, it works offline, and is compatible with both Python 2 and 3.
# Initialize the text-to-speech engine
import pyttsx3
import threading
import queue
import logging

logging.basicConfig(level=logging.INFO)

class TextToSpeechEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('voice', 'english+f3')
        self.engine.setProperty('rate', 170)
        self.engine.setProperty('volume', 1.0)
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()

    def _process_queue(self):
        while True:
            text = self.queue.get()
            if text is None:  # Signal to stop the thread
                break
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                logging.error(f"Error in TTS thread: {e}")
            finally:
                self.queue.task_done()

    def speak(self, text):
        self.queue.put(text)

    def stop(self):
        self.queue.put(None)  # Signal to stop the thread
        self.thread.join()

# Create a single instance of the TTS engine
tts_engine = TextToSpeechEngine()

# Function to speak text using the shared engine
def speak(text):
    tts_engine.speak(text)

# speak("Hello, i am a robot speaking and my name is jarvis") # Speak a message

# # Run the speech engine
# engine = pyttsx3.init() # Initialize the text-to-speech engine
# # Set the voice
# engine.setProperty('voice', 'english+f3') # Set the voice to
# # Set the speech rate
# engine.setProperty('rate', 170) # Set the speech rate
# # Set the speech volume
# engine.setProperty('volume', 1.0) # Set the speech volume
# # engine.say("Hello, i am a robot speaking and my name is jarvin") # Speak a message
# # engine.runAndWait() # Run the speech engine


