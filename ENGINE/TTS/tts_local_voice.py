import pyttsx3

class TextToSpeech:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 1.0)

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

if __name__ == "__main__":
    tts = TextToSpeech()
    tts.speak("Hello, this is a test of the local text-to-speech system.")
    tts.speak("mera name jarvis hai.")
    tts.speak("Aman ji, main ek AI assistant hoon, toh main kitni nahin ho sakta. Main hamesha aapki madad ke liye taiyaar hoon!")
