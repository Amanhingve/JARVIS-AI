#!/usr/bin/env python3
# apple_stt.py

from curses import flash
from math import e
from typing_extensions import Buffer
import objc
from Foundation import NSObject, NSBundle
from PyObjCTools import AppHelper
import time # Import the time module
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. Load the Speech framework
speech_bundle = NSBundle.bundleWithPath_(
    '/System/Library/Frameworks/Speech.framework'
)
if not speech_bundle.load():
    logger.error("Failed to load Speech framework")
    exit(1)

# 2. Lookup the Objective‑C classes we need
SFSpeechRecognizer = objc.lookUpClass('SFSpeechRecognizer')
SFSpeechAudioBufferRecognitionRequest = objc.lookUpClass(
    'SFSpeechAudioBufferRecognitionRequest'
)
AVAudioEngine = objc.lookUpClass('AVAudioEngine')
NSLocale = objc.lookUpClass('NSLocale')

# 3. Register block signatures
objc.registerMetaDataForSelector(
    b'SFSpeechRecognizer',
    b'recognitionTaskWithRequest:resultHandler:',
    {
        'retval': {'type': 'v'},
        'arguments': {
            3: {
                'callable': {
                    'retval': {'type': b'v'},
                    'arguments': {
                        0: {'type': b'@'},  # SFSpeechRecognitionResult *
                        1: {'type': b'@'}   # NSError *
                    }
                }
            }
        }
    }
)

objc.registerMetaDataForSelector(
    b'AVAudioNode', # Correct class for the method
    b'installTapOnBus:bufferSize:format:block:',
    {
        'arguments': {
            # 0: self (implicit)
            # 1: selector (implicit)
            2: {'type': b'Q'}, # bus (AVAudioNodeBus -> NSUInteger -> Q)
            3: {'type': b'I'}, # bufferSize (AVAudioFrameCount -> uint32_t -> I)
            4: {'type': b'@'}, # format (AVAudioFormat *)
            5: {              # block (AVAudioNodeTapBlock)
                'callable': {
                    'retval': {'type': b'v'}, # Block returns void
                    'arguments': {
                        # 0: block itself (implicit)
                        1: {'type': b'@'}, # buffer (AVAudioPCMBuffer *)
                        2: {'type': b'@'}  # when (AVAudioTime *) - Treat as object pointer
                    }
                }
            }
        }
    }
)

# Metadata for AVAudioEngine startAndReturnError:
objc.registerMetaDataForSelector(
    b'AVAudioEngine',
    b'startAndReturnError:',
    {
        'retval': {'type': objc._C_BOOL}, # Method returns a boolean
        'arguments': {
            # 0: self, 1: selector are implicit
            2: {'type': b'o^@', 'type_modifier': objc._C_OUT} # Argument 2 is NSError ** (out parameter)
        }
    }
)


class SpeechRecognizer(NSObject):
    def init(self):
        self = objc.super(SpeechRecognizer, self).init()
        if self is None:
            return None

        # Audio engine + request
        self.engine = AVAudioEngine.alloc().init()
        self.request = SFSpeechAudioBufferRecognitionRequest.alloc().init()
        # Give a hint that we expect dictation-style input (1 = SFSpeechRecognitionTaskHintDictation)
        self.request.setTaskHint_(1)
        self.final_result = None # Variable to store the final result
        self.recognition_error = None # Variable to store any error
        self.last_result_time = None # Time of the last partial result
        self.last_text = "" # Store the latest text
        self.timeout_timer = None # Timer object for timeout check
        self.timeout_duration = 1.5 # Seconds of silence before finalizing
        # Use en‑US locale
        locale = NSLocale.alloc().initWithLocaleIdentifier_('en-IN')
        self.recognizer = SFSpeechRecognizer.alloc().initWithLocale_(locale)
        return self

    def start(self):
        # 4. Install a tap on the mic input node
        node = self.engine.inputNode()
        fmt = node.outputFormatForBus_(0)
        
        # Make sure the block signature matches what we registered
        # The block now receives PyObjC objects directly based on metadata
        # Adjusting based on error: PyObjC seems to only pass the buffer
        def tap_block(pcm_buffer): 
            # No manual conversion needed for pcm_buffer
            self.request.appendAudioPCMBuffer_(pcm_buffer)
            logger.debug("Audio buffer appended to request.") # Simplified logging

        node.installTapOnBus_bufferSize_format_block_(
           0,           # bus
            1024,
            fmt,
            tap_block
        )

        # 5. Start the audio engine
        self.engine.prepare()
        ok, err = self.engine.startAndReturnError_(None)
        if not ok:
            logger.error(f'Audio engine failed to start: {err}')
            return

        # 6. Define the Python callback for recognition results
        # Adjusting based on error: PyObjC seems to only pass one argument
        def result_handler(arg1):
            result = None
            error = None
            # Check if the passed argument is an NSError
            if isinstance(arg1, objc.lookUpClass("NSError")):
                error = arg1
            else: # Assume it's the SFSpeechRecognitionResult
                result = arg1

            if error is not None:
                self.recognition_error = error # Store the error
                logger.error(f'Error: {error}')
                AppHelper.stopEventLoop()
                return

            # text = result.bestTranscription().formattedString()
            # # print(f"user speak:{text}") # Optional: print intermediate results
            # print(f"\ruser speak:{text}", end="", flush=True)
            # # logger.info(f'Transcribed: {text}') # Log the transcribed text

            # --- Check if result object is valid before proceeding ---
            if result:
                # --- Safely get transcription ---
                transcription = result.bestTranscription()
                # print("\rListening...", end="", flush=True)
                if transcription:
                    text = transcription.formattedString()
                    # Print intermediate results on the same line, overwriting previous
                    print(f"\ruser speak: {text}", end="", flush=True)
                    # logger.info(f'Transcribed: {text}') # Log the transcribed text

                    # --- Timeout Logic ---
                    self.last_text = text # Update last known text
                    self.last_result_time = time.time() # Record time of this result

                    # Cancel any existing timer
                    if self.timeout_timer:
                        self.timeout_timer.cancel()

                    # Schedule check_timeout to run after timeout_duration
                    # Use AppHelper.callLater for event loop integration
                    self.timeout_timer = AppHelper.callLater(self.timeout_duration, self.check_timeout)
                    # --- End Timeout Logic ---
                else:
                    # Handle case where there's a result object but no transcription
                    logger.warning("Received result object without a valid transcription.")
                    text = self.last_text # Fallback to last known text if available

                if result.isFinal():
                    # Stop once we get the final result
                    # logger.info("result.isFinal() is true.")
                    # Ensure we have valid text before finalizing
                    final_text_to_use = text if transcription else self.last_text
                    self.finalize_recognition(final_text_to_use) # Finalize
            else:
                # Handle the case where the result object itself is None
                # logger.warning("Received a None result object in result_handler.")
                # Optionally, you could trigger finalization here if None means the end
                # self.finalize_recognition(self.last_text)
                pass


        # 7. Kick off the recognition task with our block
        self.recognitionTask = self.recognizer.recognitionTaskWithRequest_resultHandler_(
            self.request,
            result_handler
        )
        # logger.info('Listening... (speak now)')
        print("\rListening...", end="", flush=True)

    def check_timeout(self):
        """Called by the timer to check if enough silence has passed."""
        if self.last_result_time and (time.time() - self.last_result_time >= self.timeout_duration):
            # logger.info(f"Timeout detected ({self.timeout_duration}s of silence). Finalizing.")
            self.finalize_recognition(self.last_text) # Finalize with the last known text
        else:
            # This can happen if a new result came in just before the timer fired
            logger.debug("Timeout check called, but silence duration not met or no results yet.")

    def finalize_recognition(self, final_text):
        try:
            """Stops recognition and the event loop."""
            if self.final_result is not None: # Already finalized
                return

            # logger.info("Finalizing recognition.")
            self.final_result = final_text # Store the final text

            # Cancel any pending timeout timer
            if self.timeout_timer:
                self.timeout_timer.cancel()
                self.timeout_timer = None

            # Stop audio processing
            if self.engine.isRunning():
                self.engine.stop()
                self.engine.inputNode().removeTapOnBus_(0) # Remove the tap

            # End the audio request (important!)
            self.request.endAudio()

            # Cancel the recognition task
            if hasattr(self, 'recognitionTask') and self.recognitionTask:
                self.recognitionTask.cancel()
                self.recognitionTask = None

            # Stop the event loop
            AppHelper.stopEventLoop()
            # logger.info("Event loop stop requested.")
            # Print the final result
            # logger.info('Listening... (speak now)')
        except Exception as e:
            pass

# Function to be called from main.py
def speech_to_text():
    """Starts Apple Speech Recognition and returns the final transcribed text."""
    try:
        recognizer = SpeechRecognizer.alloc().init()
        # print("\r" + " " * 80 + "\r", end="", flush=True) # Print spaces to overwrite
        if recognizer:
            recognizer.start()
            AppHelper.runConsoleEventLoop() # Wait here until stopEventLoop is called
            # logger.info("Event loop finished. Preparing to return result.") # Add log here
            if recognizer.recognition_error:
                # logger.error(f"Recognition failed with error: {recognizer.recognition_error}")
                return None # Or raise an exception
            print("\r" + " " * 80 + "\r", end="", flush=True) # Print spaces to overwrite
            return recognizer.final_result
        
        else:
            # logger.error("Failed to initialize SpeechRecognizer")
            return None
    except KeyboardInterrupt:
        print("Exiting...")
        return None
    except Exception as e:
        # logger.error(f'Failed to start recognition: {e}')
        return None
    


# if __name__ == '__main__':
#     while True:
#         transcribed_text = speech_to_text()
#         print("\r" + " " * 120 + "\r", end="", flush=True)
#         if transcribed_text:
#             # print(f"Final Transcription: {transcribed_text}")
#             print(f"\rOutput: {transcribed_text}")
#         if "Exit" in transcribed_text:
#             print("Exiting...")
            # break


    # print("\rListening...", end="", flush=True)
        
    # # Example usage when running the script directly
    # transcribed_text = speech_to_text()
    # # print("\r" + " " * 80 + "\r", end="", flush=True) # Print spaces to overwrite
    # if transcribed_text:
    #     print(f"Final Transcription: {transcribed_text}")