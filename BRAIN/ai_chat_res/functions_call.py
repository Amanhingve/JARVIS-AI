# In BRAIN/ai_chat_res/functions.py (create this file)
import os
import sys
import re
import logging
import subprocess
import time

import scipy as sp

from ENGINE.STT.apple_stt import speech_to_text # <-- Use Apple STT
from ENGINE.TTS.eSpeakNG_fast50ms import speak
import wave

import tkinter as tk
from tkinter import simpledialog

from BRAIN.ai_chat_res.stock.stockRealtime import get_stock_price, plot_stock_chart, extract_stock_symbol_groq
from BRAIN.ai_chat_res.RealtimeSearchEngine_groq import perform_ddg_search, GoogleSearch, RealTimeSearchEngine
from BRAIN.ai_chat_res.Chatbot import ChatBot
from BRAIN.ai_chat_res.image_gen.img_gen import generate_and_save_image as generate_image_from_hf_api

# --- Tkinter Input Helper ---
_tk_root = None
_tk_tried_appkit_init = False

# --- Globals to be set by main.py for UI mode communication ---
IS_MAIN_IN_UI_MODE = False
MAIN_UI_INPUT_MAGIC_START = "__UI_EXPECTING_INPUT_START__:" # Default, should match main.py

def set_main_ui_mode_status(is_ui_mode: bool, magic_start_string: str):
    """
    Called by main.py to inform this module about the UI mode status
    and the magic string used for prompting input.
    """
    global IS_MAIN_IN_UI_MODE, MAIN_UI_INPUT_MAGIC_START
    IS_MAIN_IN_UI_MODE = is_ui_mode
    MAIN_UI_INPUT_MAGIC_START = magic_start_string

def _get_tkinter_root():
    """Initializes and returns a hidden Tkinter root window."""
    global _tk_root, _tk_tried_appkit_init
    
    if _tk_root is None:
        # Attempt to initialize AppKit for macOS compatibility once.
        # This can help prevent crashes related to NSApplication.
        if sys.platform == "darwin" and not _tk_tried_appkit_init:
            try:
                from AppKit import NSApplication
                # This line is crucial for some Tkinter versions on macOS
                # to correctly interact with the windowing system.
                NSApplication.sharedApplication()
                logging.info("Successfully initialized NSApplication for Tkinter on macOS.")
            except ImportError:
                logging.warning(
                    "AppKit module (PyObjC) not found. Tkinter might have issues on macOS "
                    "if not run from a .app bundle or if PyObjC is not installed. "
                    "Consider installing it: pip install pyobjc"
                )
            except Exception as e:
                logging.error(f"Error during AppKit initialization for Tkinter: {e}")
            finally:
                _tk_tried_appkit_init = True 

        try:
            _tk_root = tk.Tk()
            _tk_root.withdraw() # Hide the main Tkinter window
            _tk_root.update()   # Process events, make sure window is managed
        except tk.TclError as e:
            logging.error(f"Failed to initialize Tkinter root window: {e}")
            _tk_root = None # Ensure _tk_root is None if tk.Tk() fails
    return _tk_root

def get_input_from_popup(prompt_message: str, title: str = "Input") -> str:
    """
    Gets input from the user.
    If IS_MAIN_IN_UI_MODE is True, uses stdout/stdin compatible with main.py's UI.
    Otherwise, uses a minimal cross-platform GUI input dialog (easygui) if available,
    else falls back to console input.
    """
    if IS_MAIN_IN_UI_MODE:
        effective_prompt = prompt_message if prompt_message else "Please provide input:"
        print(f"{MAIN_UI_INPUT_MAGIC_START}{effective_prompt}", flush=True)
        user_text = sys.stdin.readline().strip()
        return user_text
    try:
        import easygui
        user_input = easygui.enterbox(prompt_message, title)
        return user_input if user_input is not None else ""
    except ImportError:
        # easygui not installed, fallback to console input
        return input(f"{prompt_message}: ")
    except Exception:
        # Any other GUI error, fallback to console input
        return input(f"{prompt_message}: ")




# --- Add File Reading Imports ---
# Assuming file_reader.py is in the same directory or accessible via path
try:
    from Automation.textRead import presentation_read, pdf_read, ms_word, get_file_path
    from Automation.search_in_google import search_google
    from Automation.battery_alert import battery_alert1
    from Automation.check_battery_persentage import get_battery_percentage_advice as get_battery_advice_func
except ImportError:
    # print("Warning: Could not import file reader functions.")
    def presentation_read(query: str) -> str: return "File reading function (presentation) not available."
    def pdf_read(query: str) -> str: return "File reading function (PDF) not available."
    def ms_word(query: str) -> str: return "File reading function (Word) not available."
# --- End Add File Reading Imports ---
# --- Add WhatsApp Imports ---

# --- NEW: Import functions from open_closeWebApp.py ---
# Adjust path to go up two levels from BRAIN/ai_chat_res to the project root, then into Automation
automation_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Automation'))
if automation_path not in sys.path:
    sys.path.insert(0, automation_path)

try:
    from Automation.open_closeWebApp import (
        open_website,
        open_application,
        close_application,
        # close_current_tab_or_window # Import the new function
    )
    from Automation.adb_call import (
        # get_contact_number_google, 
        make_phone_call_adb, 
        end_call_adb, 
        check_adb_connection, 
        toggle_speaker_adb, 
        take_screenshot_adb, 
        get_battery_percentage_adb,
        get_contact_number_from_file,
        ensure_adb_connection,
        get_sim_slot_choice,
        run_adb_command
        )
    # print("Successfully imported functions from open_closeWebApp.")
    adb_available = True

    from Automation.caption_in_video import (
        volume_up, volume_down, mute_volume, unmute_volume,
        seek_forward, seek_backward, seek_forward_10s, seek_backward_10s,
        seek_backward_frame, seek_forward_frame, seek_to_beginning, seek_to_end,
        seek_to_previous_chapter, seek_to_next_chapter, move_to_next_video,
        move_to_previous_video, decrease_playback_speed, increase_playback_speed,
        toggle_subtitles, increase_font_size, decrease_font_size,
        rotate_text_opacity, rotate_window_opacity
    )
    video_control_available = True

    from Automation.pen_drive_plug_check import is_pen_drive_present
    pen_drive_check_available = True

    from Automation.Another_Automation_in_youtube import (
        pan_up, pan_down, pan_left, pan_right,
        zoom_in, zoom_out, go_to_search_box,
        toggle_play_pause, toggle_mute_unmute, toggle_full_screen,
        toggle_theater_mode, toggle_miniplayer_mode, exit_full_screen,
        toggle_party_mode, navigate_forward, navigate_backward
    )
    youtube_extra_control_available = True

    from Automation.tab_automation import (
        open_new_tab,
        close_tab, # Use close_current_tab_or_window instead
        open_browser_menu,
        zoom_in as browser_zoom_in, # Rename to avoid clash
        zoom_out as browser_zoom_out, # Rename to avoid clash
        refresh_page,
        switch_to_next_tab,
        switch_to_previous_tab,
        open_history,
        open_bookmarks,
        go_back,
        go_forward,
        open_dev_tools,
        toggle_full_screen as browser_toggle_fullscreen, # Rename to avoid clash
        open_private_window
    )
    tab_automation_available = True

except ImportError as e:
    # print(f"ERROR: Could not import from open_closeWebApp.py: {e}")
    # Define dummy functions if import fails, so the script doesn't crash
    def open_website(query: str) -> str: return "Error: open_website function not available."
    def open_application(query: str) -> str: return "Error: open_application function not available."
    def close_application(query: str) -> str: return "Error: close_application function not available."
    def close_current_tab_or_window() -> str: return "Error: close_current_tab_or_window function not available."
    def get_contact_number_google(name_query: str): return None, f"Error: Google contact search function not available: {e}"
    def check_adb_connection(): return False, [], f"ADB check unavailable: {e}"
    def make_phone_call_adb(recipient_number: str, sim_slot: int = None, target_device_id: str = None): return f"ADB call unavailable: {e}"
    def get_contact_number_from_file(name_query: str): return None, f"Local contact search unavailable: {e}"
    def end_call_adb(device_id: str = None): return False, f"ADB end call unavailable: {e}"
    def toggle_speaker_adb(device_id: str = None, speaker_on: bool = None): return False, f"ADB speaker toggle unavailable: {e}"
    def take_screenshot_adb(device_id: str = None): return False, f"ADB screenshot unavailable: {e}"
    def get_battery_percentage_adb(device_id: str = None): return False, f"ADB battery check unavailable: {e}"
    adb_available = False

    # Dummy functions for video control
    def volume_up(): pass
    def volume_down(): pass
    def mute_volume(): pass
    def unmute_volume(): pass
    def seek_forward(): pass
    def seek_backward(): pass
    def seek_forward_10s(): pass
    def seek_backward_10s(): pass
    def seek_backward_frame(): pass
    def seek_forward_frame(): pass
    def seek_to_beginning(): pass
    def seek_to_end(): pass
    def seek_to_previous_chapter(): pass
    def seek_to_next_chapter(): pass
    def move_to_next_video(): pass
    def move_to_previous_video(): pass
    def decrease_playback_speed(): pass
    def increase_playback_speed(): pass
    def toggle_subtitles(): pass
    def increase_font_size(): pass
    def decrease_font_size(): pass
    def rotate_text_opacity(): pass
    def rotate_window_opacity(): pass
    video_control_available = False

    def is_pen_drive_present(): return f"Pen drive check unavailable: {e}"
    pen_drive_check_available = False

    def pan_up(): pass
    def pan_down(): pass
    def pan_left(): pass
    def pan_right(): pass
    def zoom_in(): pass
    def zoom_out(): pass
    def go_to_search_box(): pass
    def toggle_play_pause(): pass
    def toggle_mute_unmute(): pass
    def toggle_full_screen(): pass
    def toggle_theater_mode(): pass
    def toggle_miniplayer_mode(): pass
    def exit_full_screen(): pass
    def toggle_party_mode(): pass
    def navigate_forward(): pass
    def navigate_backward(): pass
    youtube_extra_control_available = False

    def open_new_tab(): pass
    def open_browser_menu(): pass
    def browser_zoom_in(): pass
    def browser_zoom_out(): pass
    def refresh_page(): pass
    def switch_to_next_tab(): pass
    def switch_to_previous_tab(): pass
    def open_history(): pass
    def open_bookmarks(): pass
    def go_back(): pass
    def go_forward(): pass
    def open_dev_tools(): pass
    def browser_toggle_fullscreen(): pass
    def open_private_window(): pass
    tab_automation_available = False

# --- End NEW Import ---



def chat_with_chatbot(query: str) -> str:
    """
    Engage in a general conversation with the chatbot.
    
    Args:
        query (str): The user's query or statement.
    
    Returns:
        str: The chatbot's response.
    """
    return ChatBot(query)

def get_stock_price_info(query: str) -> str:
    """
    Get the current stock price for a given stock symbol.
    
    Args:
        query (str): The user's query, which should contain the stock symbol.
    
    Returns:
        str: The current stock price.
    """
    speak("Fetching the stock price for you.")
    return get_stock_price(extract_stock_symbol_groq(query))

def get_stock_chart(query: str) -> str:
    """
    Generate and display a stock chart for a given stock symbol.
    
    Args:
        query (str): The user's query, which should contain the stock symbol.
    
    Returns:
        str: A message indicating that the chart is being displayed.
    """
    speak("Generating stock chart for you.")
    return plot_stock_chart(extract_stock_symbol_groq(query))

def Real_Time_Search_Engine(query: str) -> str:
    """
    Search the web for information related to the user's query.
    
    Args:
        query (str): The user's search query.
    
    Returns:
        str: The search results.
    """
    speak("Searching the web for you.")
    return RealTimeSearchEngine(query)

def perform_duckduckgo_search(query: str) -> str:
    """
    Perform a search using DuckDuckGo and return the results.

    Args:
        query (str): The user's search query.

    Returns:
        str: The search results from DuckDuckGo.
    """
    speak("Searching DuckDuckGo for you.")
    return perform_ddg_search(query)

def perform_google_search(query: str) -> str:
    """
    Perform a search using Google and return the results.

    Args:
        query (str): The user's search query.

    Returns:
        str: The search results from Google.
    """
    speak("Searching Google for you.")
    return GoogleSearch(query)

def search_google_via_pywhatkit(query: str) -> str:
    """
    Performs a Google search using pywhatkit (opens browser).
    Note: The underlying function is interactive and will ask the user for input again via voice, potentially ignoring the provided 'query'.
    """
    try:
        # IMPORTANT: The original search_google asks the user again.
        # We pass the query here, but it will be ignored by the function's internal STT.
        # logging.info(f"Calling original search_google with query (will be ignored): '{query}'")
        search_google(query) # Call the imported function
        # Since search_google speaks but returns None, we provide text feedback
        # The feedback reflects the *intent* based on the LLM query, not necessarily the *actual* search term if the user was re-prompted.
        return f"Attempting to perform Google search via browser for '{query}' (will ask for confirmation)..."
    except Exception as e:
        # logging.error(f"Error during search_google_via_pywhatkit: {e}")
        return f"Sorry, failed to perform Google search for '{query}'. Error: {e}"
    
def get_battery_status(query: str = None) -> str:
    """
    Checks the current battery level and status.
    Ignores any query provided.
    """
    try:
        # Call the imported function which now returns a string
        return battery_alert1()
    except Exception as e:
        print(f"Error getting battery status: {e}")
        return "Sorry, I encountered an error while checking the battery status."

def get_battery_advice(query: str = None) -> str:
    """Checks the current battery percentage and provides advice based on the level."""
    try:
        return get_battery_advice_func() # Calls get_battery_percentage_advice
    except Exception as e:
        # logging.error(f"Error getting battery advice: {e}")
        print(f"Error getting battery advice: {e}")
        return "Sorry, I encountered an error while getting battery advice."

# --- !!! HELPER FUNCTION FOR ADB DEVICE ID !!! ---
# last_known_wifi_adb_address = None
def _get_adb_device_id():
    """Checks for a single, authorized ADB device and returns its ID."""
    # global last_known_wifi_adb_address # Access the global variable

    if not adb_available:
        # logging.error("ADB functionality is not available.")
        return None, "ADB functionality is not available."

    # Call the centralized function from adb_call.py
    device_id, error_msg = ensure_adb_connection()

    if error_msg:
        logging.error(f"_get_adb_device_id: Failed - {error_msg}")
        return None, error_msg
    elif device_id:
        logging.info(f"_get_adb_device_id: Using device - {device_id}")
        return device_id, None
    else:
        # Should not happen if ensure_adb_connection works correctly, but as a safeguard
        logging.error("_get_adb_device_id: ensure_adb_connection returned None, None unexpectedly.")
        return None, "An unexpected error occurred while ensuring ADB connection."

# --- !!! UPDATED/NEW ADB WRAPPER FUNCTIONS !!! ---

def initiate_adb_call(contact_query: str, sim_slot_choice: str = None):
    """
    Searches local contacts, then attempts to initiate a call via ADB.
    """
    logging.info(f"ADB Call Request: Query='{contact_query}', SIM='{sim_slot_choice}'")
    device_id, error_msg = _get_adb_device_id()
    if error_msg:
        return error_msg

    target_number = None
    number_source_message = ""

    # Basic check if query is likely a number
    if len(re.findall(r'\d', contact_query)) >= 5 and all(c in '0123456789+-() ' for c in contact_query):
        logging.info("Query looks like a phone number.")
        target_number = contact_query
        number_source_message = f"Using provided number: {target_number}"
    else:
        logging.info("Query looks like a name. Searching local contacts...")
        try:
            # Use local CSV search first
            found_number, search_message = get_contact_number_from_file(contact_query)
            logging.info(f"Local Contact search result: {search_message}")
            if found_number:
                target_number = found_number
                number_source_message = f"Using number from local contacts: {target_number}"
            else:
                # Optional: Add Google Contact search here as a fallback if needed
                # found_number_google, search_message_google = get_contact_number_google(contact_query)
                # if found_number_google: ...
                return search_message # Return message from local search (e.g., "not found")
        except Exception as e:
             logging.error(f"Error during local contact search: {e}", exc_info=True)
             return f"Error searching local contacts: {e}"

    selected_sim_slot_index = None
    if sim_slot_choice == '1': selected_sim_slot_index = 0
    elif sim_slot_choice == '2': selected_sim_slot_index = 1
    else : selected_sim_slot_index = 0 # Default to SIM 1 if not specified

    if selected_sim_slot_index is not None:
        logging.info(f"Selected SIM slot index: {selected_sim_slot_index}")
    else:
        logging.warning("No SIM slot specified. Defaulting to SIM 1.")

    if target_number:
        logging.info(f"Attempting ADB call to {target_number} on device {device_id} (SIM index {selected_sim_slot_index})")
        try:
            # Pass device_id to make_phone_call_adb
            call_result = make_phone_call_adb(target_number, sim_slot=selected_sim_slot_index, target_device_id=device_id)
            logging.info(f"ADB call function returned: {call_result}")
            return call_result
        except Exception as e:
             logging.error(f"Error during ADB call initiation: {e}", exc_info=True)
             return f"Error initiating call via ADB: {e}"
    else:
        return "Sorry, couldn't determine a valid phone number."

def end_adb_call(query: str = None): # Query ignored, added for consistency
    """Ends the current ADB-initiated phone call."""
    logging.info("ADB End Call Request")
    device_id, error_msg = _get_adb_device_id()
    if error_msg:
        return error_msg

    success, message = end_call_adb(device_id=device_id)
    return message # Return the status message from end_call_adb

def toggle_adb_speaker(speaker_on_str: str = None):
    """
    Toggles or sets the speakerphone state via ADB.
    Args: speaker_on_str (str, optional): "true" to turn on, "false" to turn off, None to toggle.
    """
    logging.info(f"ADB Speaker Toggle Request: state='{speaker_on_str}'")
    device_id, error_msg = _get_adb_device_id()
    if error_msg:
        return error_msg

    speaker_on = None
    if speaker_on_str is not None:
        if speaker_on_str.lower() == 'true':
            speaker_on = True
        elif speaker_on_str.lower() == 'false':
            speaker_on = False
        else:
            logging.warning(f"Invalid speaker_on_str value: '{speaker_on_str}'. Will toggle instead.")
            # Proceed with speaker_on = None (toggle)

    success, message = toggle_speaker_adb(device_id=device_id, speaker_on=speaker_on)
    return message # Return status message

def take_adb_screenshot(query: str = None): # Query ignored
    """Takes a screenshot via ADB and saves it on the device."""
    logging.info("ADB Screenshot Request")
    device_id, error_msg = _get_adb_device_id()
    if error_msg:
        return error_msg

    # Call the version that saves ON THE DEVICE
    success, message = take_screenshot_adb(device_id=device_id)
    return message # Return status message

def get_adb_battery_percentage(query: str = None): # Query ignored
    """Gets the battery percentage via ADB."""
    logging.info("ADB Battery Check Request")
    device_id, error_msg = _get_adb_device_id()
    if error_msg:
        return error_msg

    success, result = get_battery_percentage_adb(device_id=device_id)
    if success:
        return f"The phone battery is at {result}%."
    else:
        return f"Failed to get battery level: {result}"
# --- End ADB Wrapper Functions ---

# --- Wrapper function for Image Generation ---
def generate_image(query: str) -> str:
    """
    Wrapper function called by JARVIS for image generation.
    Generates image, saves it, attempts to open it, and returns a confirmation message.
    """
    # if not image_gen_available: # Check if import was successful
        # return "Error: Image generation functionality is currently unavailable due to an import error."
    speak("what do you want to generate? sir.")
    prompt = speech_to_text() # Convert query to text
    
    # prompt = query
    if not prompt:
        return "Error: No prompt provided for image generation."
    
    if "Exit" in prompt or "exit" in prompt or "quit" in prompt.lower() or "bye" in prompt.lower(): 
        dlg = "Exiting image generation."
        print(dlg)
        speak(dlg)
        return "Exiting image generation."
    speak(f"Generating image for prompt: {prompt}")
    logging.info(f"Calling image generation API with prompt: {prompt}")
    # Call the actual implementation function imported from img_gen.py
    # This function returns the absolute filepath on success, or an error string
    result_path_or_error = generate_image_from_hf_api(prompt)
    logging.info(f"Image generation result: {result_path_or_error}")

    # Check if the result indicates success (it's a path, not an error string starting with "Error:")
    if not result_path_or_error.startswith("Error:"):
        # Success! Construct a user-friendly message.
        # You can customize this message further.
        confirmation_message = f"Okay, I have generated the image for '{prompt}' and saved it."

        # --- Attempt to open the saved image (Optional - Keep if desired) ---
        # This part tries to open the image but doesn't affect the return message
        print(f"Attempting to open '{result_path_or_error}'...") # Keep console log for debugging
        try:
            absolute_path = os.path.abspath(result_path_or_error)
            if sys.platform == "win32":
                os.startfile(absolute_path)
            elif sys.platform == "darwin":
                subprocess.call(["open", absolute_path])
            else:
                subprocess.call(["xdg-open", absolute_path])
        except FileNotFoundError:
             logging.warning(f"Could not find command to open the image ('open' or 'xdg-open').")
             # Optionally add info to the confirmation message if opening fails
             # confirmation_message += " (I couldn't open it automatically.)"
        except Exception as e_open:
            logging.error(f"Error opening image: {e_open}")
            # Optionally add info to the confirmation message if opening fails
            # confirmation_message += f" (I couldn't open it automatically due to an error.)"
        # --- End attempt to open ---

        # --- RETURN THE CONFIRMATION MESSAGE ---
        return confirmation_message
        # --- END RETURN MODIFICATION ---

    else:
        # The result was an error message string, return it directly
        print(f"Image generation failed: {result_path_or_error}") # Keep console log for debugging
        return result_path_or_error # Return the specific error message

# --- NEW: Wrapper functions for Video Control ---
def _video_control_wrapper(func, action_name: str, query: str = None):
    """Generic wrapper for simple video control actions."""
    if not video_control_available:
        return f"Video control function ({action_name}) unavailable due to import error."
    try:
        func() # Call the imported function
        logging.info(f"Video control action executed: {action_name}")
        return f"Okay, {action_name}."
    except Exception as e:
        logging.error(f"Error executing video control '{action_name}': {e}")
        return f"Sorry, I couldn't perform the action '{action_name}'. Error: {e}"

def video_volume_up(query: str = None):
    """Increases the video player volume."""
    return _video_control_wrapper(volume_up, "increasing volume")

def video_volume_down(query: str = None):
    """Decreases the video player volume."""
    return _video_control_wrapper(volume_down, "decreasing volume")

def video_mute(query: str = None):
    """Mutes the video player volume."""
    return _video_control_wrapper(mute_volume, "muting volume")

def video_unmute(query: str = None):
    """Unmutes the video player volume."""
    return _video_control_wrapper(unmute_volume, "unmuting volume")

def video_seek_forward(query: str = None):
    """Seeks forward slightly in the video."""
    return _video_control_wrapper(seek_forward, "seeking forward")

def video_seek_backward(query: str = None):
    """Seeks backward slightly in the video."""
    return _video_control_wrapper(seek_backward, "seeking backward")

def video_seek_forward_10s(query: str = None):
    """Seeks forward 10 seconds in the video."""
    return _video_control_wrapper(seek_forward_10s, "seeking forward 10 seconds")

def video_seek_backward_10s(query: str = None):
    """Seeks backward 10 seconds in the video."""
    return _video_control_wrapper(seek_backward_10s, "seeking backward 10 seconds")

def video_seek_forward_frame(query: str = None):
    """Seeks forward one frame in the video."""
    return _video_control_wrapper(seek_forward_frame, "seeking forward one frame")

def video_seek_backward_frame(query: str = None):
    """Seeks backward one frame in the video."""
    return _video_control_wrapper(seek_backward_frame, "seeking backward one frame")

def video_seek_to_beginning(query: str = None):
    """Seeks to the beginning of the video."""
    return _video_control_wrapper(seek_to_beginning, "seeking to beginning")

def video_seek_to_end(query: str = None):
    """Seeks to the end of the video."""
    return _video_control_wrapper(seek_to_end, "seeking to end")

def video_next_chapter(query: str = None):
    """Seeks to the next chapter in the video."""
    return _video_control_wrapper(seek_to_next_chapter, "seeking to next chapter")

def video_previous_chapter(query: str = None):
    """Seeks to the previous chapter in the video."""
    return _video_control_wrapper(seek_to_previous_chapter, "seeking to previous chapter")

def video_next_video(query: str = None):
    """Moves to the next video in the playlist."""
    return _video_control_wrapper(move_to_next_video, "moving to next video")

def video_previous_video(query: str = None):
    """Moves to the previous video in the playlist."""
    return _video_control_wrapper(move_to_previous_video, "moving to previous video")

def video_increase_speed(query: str = None):
    """Increases the playback speed."""
    return _video_control_wrapper(increase_playback_speed, "increasing playback speed")

def video_decrease_speed(query: str = None):
    """Decreases the playback speed."""
    return _video_control_wrapper(decrease_playback_speed, "decreasing playback speed")

def video_toggle_subtitles(query: str = None):
    """Toggles subtitles/captions on or off."""
    return _video_control_wrapper(toggle_subtitles, "toggling subtitles")

def video_increase_font_size(query: str = None):
    """Increases the subtitle font size."""
    return _video_control_wrapper(increase_font_size, "increasing font size")

def video_decrease_font_size(query: str = None):
    """Decreases the subtitle font size."""
    return _video_control_wrapper(decrease_font_size, "decreasing font size")

def video_rotate_text_opacity(query: str = None):
    """Rotates through subtitle text opacity levels."""
    return _video_control_wrapper(rotate_text_opacity, "rotating text opacity")

def video_rotate_window_opacity(query: str = None):
    """Rotates through subtitle window opacity levels."""
    return _video_control_wrapper(rotate_window_opacity, "rotating window opacity")
# --- END NEW Video Control Wrappers ---

def check_pen_drive_status(query: str = None): # Query is ignored
    """Checks if a pen drive (USB drive) is currently connected."""
    logging.info("Pen Drive Check Request")
    if not pen_drive_check_available:
        return "Pen drive check function is unavailable due to an import error."
    try:
        # Call the function from pen_drive_plug_check.py
        result = is_pen_drive_present()
        return result # Return the string message directly
    except Exception as e:
        logging.error(f"Error during pen drive check: {e}", exc_info=True)
        return f"Sorry, I encountered an error while checking for pen drives: {e}"
    
def youtube_pan_up(query: str = None):
    """Pans the view up in YouTube 360/VR videos."""
    if not youtube_extra_control_available: return "YouTube pan control unavailable."
    return _video_control_wrapper(pan_up, "panning up")

def youtube_pan_down(query: str = None):
    """Pans the view down in YouTube 360/VR videos."""
    if not youtube_extra_control_available: return "YouTube pan control unavailable."
    return _video_control_wrapper(pan_down, "panning down")

def youtube_pan_left(query: str = None):
    """Pans the view left in YouTube 360/VR videos."""
    if not youtube_extra_control_available: return "YouTube pan control unavailable."
    return _video_control_wrapper(pan_left, "panning left")

def youtube_pan_right(query: str = None):
    """Pans the view right in YouTube 360/VR videos."""
    if not youtube_extra_control_available: return "YouTube pan control unavailable."
    return _video_control_wrapper(pan_right, "panning right")

def youtube_zoom_in(query: str = None):
    """Zooms in the view in YouTube 360/VR videos."""
    if not youtube_extra_control_available: return "YouTube zoom control unavailable."
    return _video_control_wrapper(zoom_in, "zooming in")

def youtube_zoom_out(query: str = None):
    """Zooms out the view in YouTube 360/VR videos."""
    if not youtube_extra_control_available: return "YouTube zoom control unavailable."
    return _video_control_wrapper(zoom_out, "zooming out")

def youtube_go_to_search(query: str = None):
    """Activates the search box within the YouTube page."""
    if not youtube_extra_control_available: return "YouTube search box control unavailable."
    return _video_control_wrapper(go_to_search_box, "activating search box")

def youtube_toggle_play_pause(query: str = None):
    """Toggles play/pause for the YouTube video."""
    if not youtube_extra_control_available: return "YouTube play/pause control unavailable."
    return _video_control_wrapper(toggle_play_pause, "toggling play/pause")

def youtube_toggle_mute(query: str = None):
    """Toggles mute/unmute for the YouTube video."""
    if not youtube_extra_control_available: return "YouTube mute control unavailable."
    return _video_control_wrapper(toggle_mute_unmute, "toggling mute")

def youtube_toggle_fullscreen(query: str = None):
    """Toggles fullscreen mode for the YouTube video."""
    if not youtube_extra_control_available: return "YouTube fullscreen control unavailable."
    return _video_control_wrapper(toggle_full_screen, "toggling fullscreen")

def youtube_toggle_theater_mode(query: str = None):
    """Toggles theater mode for the YouTube video."""
    if not youtube_extra_control_available: return "YouTube theater mode control unavailable."
    return _video_control_wrapper(toggle_theater_mode, "toggling theater mode")

def youtube_toggle_miniplayer(query: str = None):
    """Toggles miniplayer mode for the YouTube video."""
    if not youtube_extra_control_available: return "YouTube miniplayer control unavailable."
    return _video_control_wrapper(toggle_miniplayer_mode, "toggling miniplayer")

def youtube_exit_fullscreen(query: str = None):
    """Exits fullscreen or miniplayer mode."""
    if not youtube_extra_control_available: return "YouTube exit fullscreen control unavailable."
    return _video_control_wrapper(exit_full_screen, "exiting fullscreen/miniplayer")

def youtube_toggle_party_mode(query: str = None):
    """Toggles the 'awesome' party mode effect (YouTube Easter egg)."""
    if not youtube_extra_control_available: return "YouTube party mode control unavailable."
    return _video_control_wrapper(toggle_party_mode, "toggling party mode")

# Note: navigate_forward/backward might be too generic. Let's omit them for now
# to avoid conflicts with general browser tab navigation unless specifically requested.
# def youtube_navigate_forward(query: str = None):
#     """Navigates forward within YouTube page elements (like Tab key)."""
#     if not youtube_extra_control_available: return "YouTube navigation control unavailable."
#     return _video_control_wrapper(navigate_forward, "navigating forward")

# def youtube_navigate_backward(query: str = None):
#     """Navigates backward within YouTube page elements (like Shift+Tab key)."""
#     if not youtube_extra_control_available: return "YouTube navigation control unavailable."
#     return _video_control_wrapper(navigate_backward, "navigating backward")
# --- END NEW YouTube Extra Control Wrappers ---

def browser_open_new_tab(query: str = None):
    """Opens a new tab in the current browser window."""
    if not tab_automation_available: return "Browser tab control unavailable."
    return _video_control_wrapper(open_new_tab, "opening new tab")

# Note: Closing tab is handled by close_current_tab_or_window

def browser_open_menu(query: str = None):
    """Opens the browser's main menu (e.g., Settings/Preferences)."""
    if not tab_automation_available: return "Browser menu control unavailable."
    return _video_control_wrapper(open_browser_menu, "opening browser menu")

def browser_zoom_in_page(query: str = None): # Renamed slightly for clarity
    """Zooms in on the current browser page content."""
    if not tab_automation_available: return "Browser zoom control unavailable."
    return _video_control_wrapper(browser_zoom_in, "zooming in page") # Use renamed import

def browser_zoom_out_page(query: str = None): # Renamed slightly for clarity
    """Zooms out on the current browser page content."""
    if not tab_automation_available: return "Browser zoom control unavailable."
    return _video_control_wrapper(browser_zoom_out, "zooming out page") # Use renamed import

def browser_refresh_page(query: str = None):
    """Refreshes the current browser page."""
    if not tab_automation_available: return "Browser refresh control unavailable."
    return _video_control_wrapper(refresh_page, "refreshing page")

def browser_switch_next_tab(query: str = None):
    """Switches to the next tab in the browser window."""
    if not tab_automation_available: return "Browser tab switching unavailable."
    return _video_control_wrapper(switch_to_next_tab, "switching to next tab")

def browser_switch_previous_tab(query: str = None):
    """Switches to the previous tab in the browser window."""
    if not tab_automation_available: return "Browser tab switching unavailable."
    return _video_control_wrapper(switch_to_previous_tab, "switching to previous tab")

def browser_open_history(query: str = None):
    """Opens the browser history panel/tab."""
    if not tab_automation_available: return "Browser history control unavailable."
    return _video_control_wrapper(open_history, "opening history")

def browser_open_bookmarks(query: str = None):
    """Opens the browser bookmarks panel/manager."""
    if not tab_automation_available: return "Browser bookmarks control unavailable."
    return _video_control_wrapper(open_bookmarks, "opening bookmarks")

def browser_go_back(query: str = None):
    """Navigates back in the browser history for the current tab."""
    if not tab_automation_available: return "Browser navigation control unavailable."
    return _video_control_wrapper(go_back, "going back")

def browser_go_forward(query: str = None):
    """Navigates forward in the browser history for the current tab."""
    if not tab_automation_available: return "Browser navigation control unavailable."
    return _video_control_wrapper(go_forward, "going forward")

def browser_open_dev_tools(query: str = None):
    """Opens the browser's developer tools panel."""
    if not tab_automation_available: return "Browser dev tools control unavailable."
    return _video_control_wrapper(open_dev_tools, "opening developer tools")

def browser_toggle_fullscreen_window(query: str = None): # Renamed slightly for clarity
    """Toggles fullscreen mode for the entire browser window."""
    if not tab_automation_available: return "Browser fullscreen control unavailable."
    return _video_control_wrapper(browser_toggle_fullscreen, "toggling browser fullscreen") # Use renamed import

def browser_open_private_window(query: str = None):
    """Opens a new private/incognito browser window."""
    if not tab_automation_available: return "Browser private window control unavailable."
    return _video_control_wrapper(open_private_window, "opening private window")
# --- End Browser Tab Automation Wrappers ---

def read_presentation(query: str = None): # Accept optional query, but ignore it
    """Reads the content of a PowerPoint presentation. Prompts user for file path."""
    speak("Please enter the presentation's name or full path.")
    # location = input("Enter the presentation's name or full path: ")
    location = get_input_from_popup("Enter the presentation's name or full path:", title="Read Presentation")

    if not location: # User cancelled or entered nothing
        return "No file path provided by user. Cannot read presentation."
    
    file_path_or_name = get_file_path(location)
    if not file_path_or_name:
        return "No file path provided. Cannot read presentation."
    logging.info(f"Attempting to read presentation: {file_path_or_name}")
    return presentation_read(file_path_or_name)

def read_pdf(query: str = None): # Accept optional query, but ignore it
    """Reads the content of a PDF file. Prompts user for file path."""
    speak("Please enter the PDF's name or full path.")
    # location = input("Enter the presentation's name or full path: ")
    location = get_input_from_popup("Enter the PDF's name or full path:", title="Read PDF")

    if not location: # User cancelled or entered nothing
        return "No file path provided by user. Cannot read PDF."

    file_path_or_name = get_file_path(location)
    if not file_path_or_name:
        return "No file path provided. Cannot read PDF."
    logging.info(f"Attempting to read PDF: {file_path_or_name}")
    return pdf_read(file_path_or_name)

def read_word(query: str = None): # Accept optional query, but ignore it
    """Reads the content of a Word document. Prompts user for file path."""
    speak("Please enter the Word document's name or full path.")
    # location = input("Enter the presentation's name or full path: ")
    location = get_input_from_popup("Enter the Word document's name or full path:", title="Read Word Document")

    if not location: # User cancelled or entered nothing
        return "No file path provided by user. Cannot read Word document."
       
    file_path_or_name = get_file_path(location)
    if not file_path_or_name:
        return "No file path provided. Cannot read Word document."
    logging.info(f"Attempting to read Word document: {file_path_or_name}")
    return ms_word(file_path_or_name)
# Add more functions here as needed...

# Dictionary to map function names to their actual functions
available_functions = {
    "chat_with_chatbot": chat_with_chatbot,
    "get_stock_price_info": get_stock_price_info,
    "get_stock_chart": get_stock_chart,
    "Real_Time_Search_Engine": Real_Time_Search_Engine,
    "perform_duckduckgo_search": perform_duckduckgo_search,
    "perform_google_search": perform_google_search,

    "presentation_read": read_presentation,
    "pdf_read": read_pdf,
    "ms_word": read_word,

    # --- NEW: Add open/close functions ---
    "open_website": open_website,
    "open_application": open_application,
    "close_application": close_application,
    # "close_current_tab": close_current_tab_or_window, # Use a clear name for the AI
    "close_current_tab": close_tab, # Use a clear name for the AI

    # --- End NEW ---
    "search_google_pywhatkit": search_google_via_pywhatkit, # Use this for browser-opening search
    "get_battery_status": get_battery_status,
    "get_battery_advice": get_battery_advice, # New function (from check_battery_persentage.py)
    "generate_image": generate_image,

    # --- NEW ADB FUNCTIONS ---
    "initiate_adb_call": initiate_adb_call, # Updated wrapper
    "end_adb_call": end_adb_call,
    "toggle_adb_speaker": toggle_adb_speaker,
    "take_adb_screenshot": take_adb_screenshot,
    "get_adb_battery_percentage": get_adb_battery_percentage,

    # --- NEW: Add Video Control Functions ---
    "video_volume_up": video_volume_up,
    "video_volume_down": video_volume_down,
    "video_mute": video_mute,
    "video_unmute": video_unmute,
    "video_seek_forward": video_seek_forward,
    "video_seek_backward": video_seek_backward,
    "video_seek_forward_10s": video_seek_forward_10s,
    "video_seek_backward_10s": video_seek_backward_10s,
    "video_seek_forward_frame": video_seek_forward_frame,
    "video_seek_backward_frame": video_seek_backward_frame,
    "video_seek_to_beginning": video_seek_to_beginning,
    "video_seek_to_end": video_seek_to_end,
    "video_next_chapter": video_next_chapter,
    "video_previous_chapter": video_previous_chapter,
    "video_next_video": video_next_video,
    "video_previous_video": video_previous_video,
    "video_increase_speed": video_increase_speed,
    "video_decrease_speed": video_decrease_speed,
    "video_toggle_subtitles": video_toggle_subtitles,
    "video_increase_font_size": video_increase_font_size,
    "video_decrease_font_size": video_decrease_font_size,
    "video_rotate_text_opacity": video_rotate_text_opacity,
    "video_rotate_window_opacity": video_rotate_window_opacity,
    # --- END NEW Video Control Functions ---

    "check_pen_drive_status": check_pen_drive_status,

    # --- NEW: YouTube Extra Control Functions ---
    "youtube_pan_up": youtube_pan_up,
    "youtube_pan_down": youtube_pan_down,
    "youtube_pan_left": youtube_pan_left,
    "youtube_pan_right": youtube_pan_right,
    "youtube_zoom_in": youtube_zoom_in,
    "youtube_zoom_out": youtube_zoom_out,
    "youtube_go_to_search": youtube_go_to_search,
    "youtube_toggle_play_pause": youtube_toggle_play_pause,
    "youtube_toggle_mute": youtube_toggle_mute,
    "youtube_toggle_fullscreen": youtube_toggle_fullscreen,
    "youtube_toggle_theater_mode": youtube_toggle_theater_mode,
    "youtube_toggle_miniplayer": youtube_toggle_miniplayer,
    "youtube_exit_fullscreen": youtube_exit_fullscreen,
    "youtube_toggle_party_mode": youtube_toggle_party_mode,
    # "youtube_navigate_forward": youtube_navigate_forward, # Omitted for now
    # "youtube_navigate_backward": youtube_navigate_backward, # Omitted for now

    "browser_open_new_tab": browser_open_new_tab,
    "browser_open_menu": browser_open_menu,
    "browser_zoom_in_page": browser_zoom_in_page,
    "browser_zoom_out_page": browser_zoom_out_page,
    "browser_refresh_page": browser_refresh_page,
    "browser_switch_next_tab": browser_switch_next_tab,
    "browser_switch_previous_tab": browser_switch_previous_tab,
    "browser_open_history": browser_open_history,
    "browser_open_bookmarks": browser_open_bookmarks,
    "browser_go_back": browser_go_back,
    "browser_go_forward": browser_go_forward,
    "browser_open_dev_tools": browser_open_dev_tools,
    "browser_toggle_fullscreen_window": browser_toggle_fullscreen_window,
    "browser_open_private_window": browser_open_private_window,

    # Add more functions here...
}
