import whisper
import pyaudio
import numpy as np
import threading
import queue

class WhisperSTT:
    def __init__(self, model_name="small", device="cpu", rate=16000, chunk=1024):
        """
        Initializes the WhisperSTT class.

        Args:
            model_name (str): The name of the Whisper model to load.
            device (str): The device to use for inference ("cpu" or "cuda").
            rate (int): The audio sample rate.
            chunk (int): The number of frames per buffer.
        """
        # Load Whisper model
        self.model = whisper.load_model(model_name, device=device)
        self.RATE = rate
        self.CHUNK = chunk
        self.running = False
        self.result_queue = queue.Queue()

        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        self.stream = None

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """
        Callback function for PyAudio stream.

        Args:
            in_data (bytes): Audio data.
            frame_count (int): Number of frames in the data.
            time_info (dict): Time information.
            status (int): Status flags.

        Returns:
            tuple: Audio data and flags.
        """
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        audio_data = audio_data.astype(np.float32) / 32768.0
        result = self.model.transcribe(audio_data)
        if result["text"].strip():
            self.result_queue.put(result["text"])
        return (in_data, pyaudio.paContinue)

    def listen(self):
        """
        Starts listening to the audio stream and transcribing speech.
        """
        print("🎤 Listening... (Whisper STT Enabled)")
        self.running = True
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            stream_callback=self._audio_callback
        )
        self.stream.start_stream()
        while self.running:
            pass
        self.close()

    def get_result(self):
        """
        Retrieves the transcribed text from the queue.

        Returns:
            str: The transcribed text, or None if the queue is empty.
        """
        if not self.result_queue.empty():
            return self.result_queue.get()
        return None

    def stop(self):
        """
        Stops the listening process.
        """
        self.running = False

    def close(self):
        """
        Closes the audio stream and terminates PyAudio.
        """
        if self.stream and self.stream.is_active():
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()

def speech_to_text():
    """
    Creates a WhisperSTT instance, starts listening in a separate thread,
    and returns the transcribed text.

    Returns:
        str: The transcribed text.
    """
    listener = WhisperSTT()
    
    # Create and start the listening thread
    listen_thread = threading.Thread(target=listener.listen, daemon=True)
    listen_thread.start()

    try:
        while True:
            result = listener.get_result()
            if result:
                print(f"🗣️ You said: {result}")
                return result
    except KeyboardInterrupt:
        print("\nTerminating the listener.")
        listener.stop()
        listen_thread.join()
        return ""
    finally:
        listener.close()

# if __name__ == "__main__":
#     speech_to_text()
