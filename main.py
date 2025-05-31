# In main.py
import os
from re import I

from sympy import im
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"  # Hide pygame welcome message
os.environ["Device_set_to_use_cpu"] = "hide"  # Set the device to "cpu" hide
# from ENGINE.STT.Vosk_offline import speech_to_text
# from ENGINE.STT.speechToText_googleOnline import speech_to_text

# from ENGINE.STT.NetHyTech import speech_to_text
# from ENGINE.STT.fast_stt import speech_to_text
from ENGINE.STT.apple_stt import speech_to_text # <-- Use Apple STT

# from ENGINE.STT.stt_trans import speech_to_text
# from ENGINE.STT.new_fast_stt import speech_to_text
# from ENGINE.STT.webrtcSTT import speech_to_text
# from ENGINE.STT.speech import speech_to_text
# from ENGINE.STT.noiseStt import speech_to_text

# from ENGINE.TTS.textToSpeech_pyttsx3 import speak
# from ENGINE.TTS.textToSpeech_b import speak
# from ENGINE.TTS.tts_mp3 import speak
# from ENGINE.TTS.TTS_DF import speak
# from ENGINE.TTS.fast_TTS_DF import speak
# from ENGINE.TTS.speechify import speak
# from ENGINE.TTS.deepAI import speak
from ENGINE.TTS.eSpeakNG_fast50ms import speak
import concurrent.futures
# from modules.web import open_website, search_google, close_tab  # Import functions from web module
import datetime
import time
import threading
import multiprocessing
import queue
import random
# from BRAIN.model2 import FirstLayerDMM
# from BRAIN.model import generate_response, predict_query_type
# from BRAIN.ai_chat_res.Chatbot import ChatBot
from BRAIN.ai_chat_res.RealtimeSearchEngine_groq import Information
from BRAIN.ai_chat_res.Chatbot import ChatBot
from Data.DLG import res1, res_bye

from Automation.pen_drive_plug_check import pen_drive_connected
from Automation.battery_plug_check import check_plugin_status
from Automation.battery_alert import battery_alert



import logging # import log

# setup log
logging.basicConfig(filename='main.log', level=logging.WARNING, 
        format='%(asctime)s - %(levelname)s - %(message)s')

import json
from BRAIN.ai_chat_res.functions_call import available_functions
import BRAIN.ai_chat_res.functions_call as functions_module # Import the module itself
from BRAIN.ai_chat_res.system_prompts import get_function_calling_system_prompt
#  --Authentication--
from BRAIN.auth.recoganize import AuthenticateFace

from groq import Groq
import argparse
import sys
from dotenv import dotenv_values

# Load environment variables from .env file
env_vars = dotenv_values(".env")

# Access environment variables
GroqAPIKey = env_vars.get("GroqAPIKey")
USER = os.getenv("user", "Sir")
AI_NAME = os.getenv("ai_name", "Jarvis").lower()


# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# ... (rest of your imports) ...
# --- UI Input Magic Strings ---
UI_INPUT_MAGIC_START = "__UI_EXPECTING_INPUT_START__:" # Note the colon

# Global flag to indicate if running in UI mode
IS_UI_MODE = False

# Global variable to control the hotword detection loop
# hotword_detection_running = True
def wake_word_detect():
    """Continuously listens for the wake word to activate commands."""
    speak(f"Hello, I am {AI_NAME}. Say my name to activate me.")
    
    while True:
        text = speech_to_text()
        if text and AI_NAME in text or "jarvis" in text or "Jarvis" in text or "JARVIS" in text or "Hey Jarvis" in text or "Hey jarvis" in text:
            speak("Yes sir?")
            main_loop()
        if "Exit" in text or "exit" in  text or "quit" in text.lower() or "bye" in text.lower():
            speak("Goodbye sir.")
            break
        elif text:
            speak(f"Sorry {USER}, I only respond to my name.")

def get_input_from_user(prompt: str) -> str:
    """
    Gets input from the user.
    If in UI mode, prints a magic string for ui.py to catch and reads from stdin.
    Otherwise, uses standard input().
    """
    global IS_UI_MODE
    if IS_UI_MODE:
        # print(f"{UI_INPUT_MAGIC_START}{prompt}", flush=True)
        effective_prompt = prompt if prompt else "Please provide input:"
        print(f"{UI_INPUT_MAGIC_START}{effective_prompt}", flush=True)
        # Debug: eprint(f"main.py: Sent prompt, waiting for stdin: {prompt}", file=sys.stderr, flush=True)
        user_text = sys.stdin.readline().strip()
        # Debug: eprint(f"main.py: Received from stdin: {user_text}", file=sys.stderr, flush=True)
        return user_text
    else:
        # For non-UI mode (direct terminal execution)
        return input(prompt + " ") # Add space for better terminal prompt

# def main():
#     # speak("active now jarvis")
#     # detect_hotword()
#     main_loop()


def output_text(text):
    def print_output_and_speak(t):
        # speak(t)
        print("Jarvis:", t)
        speak(t)
    # Use a lambda to capture the argument and call the inner function.
    thread_speak = threading.Thread(target=lambda: print_output_and_speak(text))
    # thread_speak = threading.Thread(target=print_output_and_speak)
    # thread_print = threading.Thread(target=print_output())
    thread_speak.daemon = True
    # thread_print.daemon = True
    thread_speak.start()
    # thread_print.start()
    # thread_speak.start()
    # Optionally join threads if you need to synchronize further execution
    thread_speak.join()
    # thread_print.join()

# def stt():
#     result_queue = queue.Queue()

#     def thread_wrapper():
#         result = speech_to_text()  # Call without passing any argument
#         # result_queue.put(result)
#         return result

#     thread = threading.Thread(target=thread_wrapper)
#     thread.daemon = True
#     thread.start()
#     thread.join()
#     return result_queue.get()
    

def main_loop():
    # global hotword_detection_running
    MAX_INACTIVITY_TIME = 10  # Auto-sleep after inactivity
    last_command_time = time.time()

    function_calling_system_prompt = get_function_calling_system_prompt()
    try:

        while True:
            # --- Check for inactivity at the beginning of each loop iteration ---
            current_time = time.time()
            if current_time - last_command_time > MAX_INACTIVITY_TIME:
                # speak("No response detected. Going to sleep.")
                # output_text("No response detected. Going to sleep.") # Also print
                return # Exit the main_loop function
            speech = "" # Initialize speech
            if IS_UI_MODE:
                # In UI mode, input comes from stdin (sent by ui.py)
                # ui.py already prints "You: [text_from_ui]"
                # main.py reads this text as the user's command.
                # print("DEBUG: main.py waiting for stdin...", file=sys.stderr, flush=True) # For debugging
                speech = sys.stdin.readline().strip()
                # print(f"DEBUG: main.py received from stdin: '{speech}'", file=sys.stderr, flush=True) # For debugging

                if not speech:
                    # If ui.py sends an empty line (e.g. user cancels input, or on initial empty send),
                    # we might want to just loop back and wait for more input.
                    output_text("Received no input from UI.") # Optional: send a message back
                # No need to print "human: " here, as ui.py handles the "You: " part.
            else:
                # In non-UI mode (terminal), use speech_to_text
                speech = speech_to_text()
                print("human: ", speech) # Print "human:" only in non-UI mode
            
            # Common processing for speech from either UI or STT
            if not speech: # Handle case where STT returns None or UI sends empty after all
                if not IS_UI_MODE: # Only show this for STT failures, UI handles its own empty input
                    output_text("Sorry, I didn't catch that. Could you please repeat?")
                continue # Skip the rest of the loop and listen/wait again
            
            if "Exit" in speech or "exit" in speech or "quit" in speech.lower() or "bye" in speech.lower():
                dlg = random.choice(res_bye)
                output_text(dlg)
                break
            
            # Function calling logic
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": Information()},
                    {"role": "system", "content": function_calling_system_prompt},
                    {"role": "user", "content": speech}
                ],
                temperature=0.7,
                max_tokens=1024,
                # max_tokens=2000,
                top_p=1,
                stream=False,
                stop=None
            )

            response_content = completion.choices[0].message.content
            # print("AI Response:", response_content)

            try:
                # Attempt to parse the response as JSON
                function_call = json.loads(response_content)
                function_name = function_call["function"]
                query = function_call["query"]

                # Check if the function exists
                if function_name in available_functions:
                    function_to_call = available_functions[function_name]
                    result = function_to_call(query)
                    output_text(result)
                else:
                    result = f"Function '{function_name}' not found."
                    output_text(result)

            except json.JSONDecodeError:
                # If not JSON, treat it as a direct response
                # output_text(response_content)
                # If not JSON, it means the LLM failed to use a tool or format its response correctly.
                # Fallback to using ChatBot with the original user's speech.
                logging.warning(f"LLM response was not valid JSON: '{response_content}'. Falling back to ChatBot with original speech: '{speech}'")
                result = ChatBot(speech) # Directly use ChatBot with the original user speech
                output_text(result)

    except KeyboardInterrupt:
        print("Program terminated by the user.")
    except Exception as e:
        print(f"Error: {e}")

def main():
    # # --- Authentication Check ---
    # speak("Please authenticate.")
    global IS_UI_MODE # Declare intent to modify global

    parser = argparse.ArgumentParser(description="Jarvis AI Assistant")
    parser.add_argument("--ui-mode", action="store_true", help="Run in UI mode, bypassing initial hotword detection and enabling UI input.")
    args = parser.parse_args()

    if args.ui_mode:
        IS_UI_MODE = True # Set the global flag

    functions_module.set_main_ui_mode_status(IS_UI_MODE, UI_INPUT_MAGIC_START)

    output_text("Please authenticate.")
    try:
        auth_status = AuthenticateFace()
        # auth_status = 1 # Uncomment for testing without camera/auth
    except Exception as auth_exc:
         logging.error(f"Error during face authentication: {auth_exc}", exc_info=True)
         speak("Sorry, there was an error during authentication.")
         print(f"Authentication Error: {auth_exc}")
         auth_status = 0 # Treat error as failure

    if auth_status != 1:
        speak("Authentication failed. Exiting.")
        print("Authentication failed. Exiting.")
        return # Stop execution if auth fails
    # --- End Authentication ---

    # speak("Authentication successful. Starting Jarvis.")
    # logging.info("Authentication successful. Starting background tasks and main loop.")
    listener_thread = None # Initialize
    # if IS_UI_MODE:
    if args.ui_mode:
        # output_text("Authentication successful. Jarvis is active.")
        # logging.info("Authentication successful. UI mode active.")
        # dlg = random.choice(res1)
        # # speak(dlg)
        # output_text(dlg)
        try:
            wake_word_detect() # Run main interaction loop once for UI
        except KeyboardInterrupt:
            print("UI mode interaction interrupted by user.")
            logging.info("KeyboardInterrupt in main_loop (UI mode).")
        # After main_loop finishes in UI mode, this instance of main.py is done.
    else:
        # Standalone mode with hotword detection (your existing hotword logic would go here)
        output_text("Authentication successful. Jarvis is in standby mode (hotword simulation).")
        logging.info("Authentication successful. Standalone mode (hotword simulation).")

        dlg = random.choice(res1)
        # speak(dlg)
        output_text(dlg)
        # This is where you'd integrate your actual hotword listener.
        # For now, let's just run main_loop once for testing standalone.
        # In a real scenario, you'd have a loop waiting for the hotword.
        print("Standalone mode: Simulating direct run of main_loop without hotword for now.")
        try:
            wake_word_detect() # This would be your hotword detection loop
        except KeyboardInterrupt:
            print("Program terminated by the user (standalone mode).")
            logging.info("KeyboardInterrupt in main_loop (standalone mode).")


    # --- Start Background Tasks in Threads ---
    # Use daemon=True so they exit automatically when the main thread exits
    thread_battery_alert = threading.Thread(target=battery_alert, daemon=True)
    thread_plugin_check = threading.Thread(target=check_plugin_status, daemon=True)
    thread_pen_drive = threading.Thread(target=pen_drive_connected, daemon=True)

    thread_battery_alert.start()
    thread_plugin_check.start()
    thread_pen_drive.start()

    # --- Start Main Conversational Loop (can be in main thread or its own thread) ---
    # Running main_loop directly in the main thread after auth is fine
    # main_loop()

    # --- Cleanup/Exit Message ---
    logging.info("Main loop finished. Background threads will exit.")
    print("Jarvis is shutting down.")
    output_text("Jarvis is shutting down.")


# --- Entry Point ---
if __name__ == "__main__":
    main()

# def jarvis():
#     t1 = threading.Thread(target=main)
#     t2 = threading.Thread(target=battery_alert)
#     t3 = threading.Thread(target=check_plugin_status)
#     t4 = threading.Thread(target=battery_alert)
#     t5 = threading.Thread(target=pen_drive_connected)
#     t1.start()
#     t2.start()
#     t3.start()
#     t4.start()
#     t5.start()
#     t1.join()
#     t2.join()
#     t3.join()
#     t4.join()
#     t5.join()


# jarvis()

# if __name__ == "__main__":
#     main()

    # stt()
    


















# ------------------- main loop -------------------

# def main_loop():
    
#     first_layer_dmm = FirstLayerDMM()  # No arguments needed during initialization
#     try:
#         dlg = random.choice(res1)
#         speak(dlg)
#         while True:
#             speech = speech_to_text().lower()
#             print("human: ", speech)
#             Decision = first_layer_dmm(speech)
#             # Decision = generate_response(speech)
#             # Decision = predict_query_type(speech).lower()
#             print("Decision: ", Decision)
#             # print("Jarvis:" , result)
#             if "exit" in Decision:
#                 # print("human: ", speech)  # The actual printing is handled within the function now
#                 dlg = random.choice(res_bye)
#                 print("Jarvis: ", dlg)
#                 speak(dlg)
#                 # print("Jarvis: Goodbye!")
#                 # speak("Goodbye!")
#                 break
#             result = ChatBot(speech) if "general" in Decision else RealTimeSearchEngine(speech) if "realtime" in Decision else None
#             print("Jarvis:", result)
#             speak(result)
#     except KeyboardInterrupt:
#         print("Program terminated by the user.")
#     except Exception as e:
#         print(f"Error: {e}")

# def main():
#     speak("active now jarvis version 1.0")
#     main_loop()

# if __name__ == "__main__":
#     main()
