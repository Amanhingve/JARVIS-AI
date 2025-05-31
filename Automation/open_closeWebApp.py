# Automation/open_closeWebApp.py

# Automation/open_closeWebApp.py

#!/usr/bin/env python3
import webbrowser
import os
import sys
import subprocess
import re
from dotenv import dotenv_values
import cohere
import logging
import pyautogui # <-- Import pyautogui

# --- Data Import ---
# Assuming Data directory is at the same level as Automation directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
try:
    from Data.Open_website_D_set import websites as common_sites_dict # Import the large dictionary
except ImportError:
    logging.error("Could not import websites from Data.Open_website_D_set.py. Using a limited default set.")
    # Fallback to a smaller dictionary if import fails
    common_sites_dict = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "facebook": "https://www.facebook.com",
        "twitter": "https://www.twitter.com",
        "wikipedia": "https://www.wikipedia.org",
        "amazon": "https://www.amazon.com",
        "reddit": "https://www.reddit.com",
        "github": "https://www.github.com",
        "chatgpt": "https://chat.openai.com",
    }


# --- Configuration ---
env_path = os.path.join(project_root, '.env') # Use project_root
env_vars = dotenv_values(env_path)
cohereAPIKey = env_vars.get("cohereAPIKey")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Cohere Client
co = None
if cohereAPIKey:
    try:
        co = cohere.Client(cohereAPIKey)
        logging.info("Cohere client initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize Cohere client: {e}")
        co = None
else:
    logging.warning("Cohere API Key not found in .env file. Cohere extraction will be skipped.")

# --- Target Extraction Functions ---

def extract_target_with_cohere(query: str, target_type: str) -> str | None:
    """
    Uses Cohere AI to extract the target (URL or App Name) from the query.
    Returns the extracted target or None if extraction fails.
    """
    if not co:
        logging.warning("Cohere client not available. Skipping Cohere extraction.")
        return None

    if target_type == "website":
        description = "website URL or common website name (e.g., 'google.com', 'youtube', 'github')"
    elif target_type == "app":
        description = "application name (e.g., 'Notepad', 'Chrome', 'Visual Studio Code', 'Music')"
    else: # Generic 'name' type
        description = "target name or identifier (e.g., 'my_document.txt', 'settings')"

    prompt = f"""
From the user's query, extract *only* the specific {description} they want to interact with.
The user's intent is related to the action type: '{target_type}'.

User Query: "{query}"

Examples:
- Query: "open google.com", Type: "website" -> Target: "google.com"
- Query: "visit youtube", Type: "website" -> Target: "youtube"
- Query: "web youtube", Type: "website" -> Target: "youtube"
- Query: "open google", Type: "website" -> Target: "google"
- Query: "open youtube", Type: "website" -> Target: "youtube"
- Query: "launch youtube", Type: "website" -> Target: "youtube"
- Query: "Can you visit reddit.com please?", Type: "website" -> Target: "reddit.com"
- Query: "website open github", Type: "website" -> Target: "github"
- Query: "start Notepad", Type: "app" -> Target: "Notepad"
- Query: "I want to close Visual Studio Code", Type: "app" -> Target: "Visual Studio Code"
- Query: "terminate the calculator app", Type: "app" -> Target: "Calculator"
- Query: "open music", Type: "app" -> Target: "Music"
- Query: "find report.docx", Type: "name" -> Target: "report.docx"
- Query: "go to the settings", Type: "app" -> Target: "Settings"
- Query: "open website github google time", Type: "website" -> Target: "github" # Prioritize first relevant target

Return *only* the extracted target name or URL. If no specific target can be reliably identified, return "NONE".
Target:"""
    try:
        logging.info(f"Attempting Cohere extraction for query: '{query}', type: '{target_type}'")
        response = co.chat(
            model='command-r', # Or 'command-r-plus'
            message=prompt,
            temperature=0.1,
            max_tokens=50,
        )
        extracted = response.text.strip().strip('\'" .,')
        logging.info(f"Cohere raw response: '{extracted}'")

        if extracted and extracted.upper() != "NONE":
            logging.info(f"Cohere successfully extracted target: '{extracted}'")
            # Basic post-processing for app names
            if target_type == "app" and not extracted[0].isupper() and ' ' in extracted: # Capitalize multi-word apps if needed
                 extracted = " ".join(part.capitalize() for part in extracted.split())
            elif target_type == "app" and not extracted[0].isupper(): # Capitalize single-word apps
                 extracted = extracted.capitalize()
            return extracted
        else:
            logging.warning(f"Cohere could not reliably extract target from '{query}'. Response: '{extracted}'")
            return None

    except Exception as e:
        logging.error(f"Error during Cohere API call for extraction: {e}")
        return None

def extract_target(query: str, target_type: str) -> str | None: # Changed return type
    """
    Attempts to extract the target (URL, App Name, etc.) using Cohere first,
    then falls back to regex/keyword extraction if necessary. Returns None if failed.
    """
    cohere_target = extract_target_with_cohere(query, target_type)
    if cohere_target:
        return cohere_target

    logging.warning(f"Falling back to regex/keyword extraction for query: '{query}'")
    try:
        action_words = []
        # Define action words specific to the type
        if target_type == "website":
            action_words = ["open", "launch", "go to", "visit", "browse", "website open", "open website"] # Added variations
            # Try simple URL regex first within the *whole* query for websites
            url_match = re.search(r'([a-zA-Z0-9-]+\.[a-zA-Z]{2,}(\.[a-zA-Z]{2,})?)', query)
            if url_match:
                logging.info(f"Regex/Keyword extracted URL target: '{url_match.group(0)}'")
                return url_match.group(0)
        elif target_type == "app":
            action_words = ["open", "launch", "start", "run", "close", "quit", "terminate", "kill", "app open", "open app", "app close", "close app"] # Added variations
        else: # Generic name
            action_words = ["open", "launch", "start", "run", "close", "quit", "terminate", "kill", "find", "get", "show", "go to", "visit", "browse"]

        words = query.lower().split()
        target_parts = []
        processed_indices = set()

        # Remove action words and common filler words first
        potential_target_words = []
        skip_next = 0
        for i, word in enumerate(words):
            if skip_next > 0:
                skip_next -= 1
                continue

            # Check for multi-word action phrases
            matched_action = False
            for action in sorted(action_words, key=len, reverse=True):
                action_parts_list = action.split()
                action_len = len(action_parts_list)
                if words[i : i + action_len] == action_parts_list:
                    skip_next = action_len - 1
                    matched_action = True
                    break
            if matched_action:
                continue

            # Check for single action words
            if word in action_words:
                 continue

            # Remove common filler/trailing words
            common_trailing = ["app", "application", "please", "for", "me", "website", "site", "the"]
            if word.strip('?.!') in common_trailing:
                continue

            potential_target_words.append(words[i]) # Keep the original case word

        if not potential_target_words:
             logging.warning(f"No potential target words left after cleaning '{query}'")
             return None # No target found

        target = " ".join(potential_target_words)

        # Specific post-processing based on type
        if target_type == "website":
            # Handle "google dot com" case
            target_lower_parts = target.lower().split()
            if len(target_lower_parts) >= 3 and target_lower_parts[-2] == "dot":
                 target = f"{target_lower_parts[-3]}.{target_lower_parts[-1]}"
            # If it still doesn't look like a URL, return it as is (might be a name like 'youtube')
        elif target_type == "app":
            # Capitalize appropriately for app names
            target = " ".join(part.capitalize() for part in target.split())

        if target:
            logging.info(f"Regex/Keyword extracted target: '{target.strip()}'")
            return target.strip()
        else:
            logging.warning(f"Regex/Keyword extraction failed for '{query}' after cleaning.")
            return None # Explicitly return None if fallback fails

    except Exception as e:
        logging.error(f"Error during regex/keyword extraction: {e}")
        return None # Return None on error

# --- Open/Close Functions ---

def open_website(query: str) -> str:
    """
    Opens a website based on the user query by extracting the target URL or name.
    """
    target = extract_target(query, "website")
    if not target:
        # If extraction completely failed, try a simple cleanup of the original query
        cleaned_query = query.lower().replace("open", "").replace("launch", "").replace("go to", "").replace("visit", "").replace("browse", "").replace("website", "").strip()
        if not cleaned_query:
            return "Please specify which website to open."
        target = cleaned_query
        logging.warning(f"Extraction failed, using cleaned query '{target}' as target.")


    # Prepend https:// if missing and it looks like a domain
    if not target.startswith(('http://', 'https://')) and '.' in target and not target.lower() in common_sites_dict:
        url = f"https://www.{target}"
    elif target.startswith(('http://', 'https://')):
        url = target # Already a full URL
    else:
        # Check the large dictionary of common sites (case-insensitive)
        url = common_sites_dict.get(target.lower())
        if not url:
             # If it's not a common name and doesn't look like a URL, search Google
             if '.' not in target and not target.startswith(('http://', 'https://')):
                 logging.info(f"Target '{target}' not in common sites and not a URL, searching Google.")
                 try:
                     # Ensure the URL includes www if it's missing from the dict value
                     search_url = f"https://www.google.com/search?q={target.replace(' ', '+')}"
                     webbrowser.open(search_url)
                     return f"Searching Google for {target}..."
                 except Exception as e:
                     logging.error(f"Error searching Google for '{target}': {e}")
                     return f"Sorry, I couldn't open or search for '{target}'. Error: {e}"
             else:
                 # Assume it might be a URL without http, e.g. "example.org"
                 url = f"https://{target}"
        else:
             # Ensure the URL includes https:// if missing from the dict value
             if not url.startswith(('http://', 'https://')):
                 url = f"https://{url}"


    try:
        logging.info(f"Attempting to open URL: {url}")
        webbrowser.open(url)
        # Use the original extracted target for the confirmation message
        display_name = target.capitalize() if target.lower() in common_sites_dict else target
        return f"Opening {display_name}..."
    except Exception as e:
        logging.error(f"Error opening website {target} with URL {url}: {e}")
        return f"Sorry, I couldn't open the website {target}. Error: {e}"

def open_application(query: str) -> str:
    """
    Opens a local application based on the user query by extracting the application name.
    """
    app_name = extract_target(query, "app")
    if not app_name:
         # If extraction completely failed, try a simple cleanup
         cleaned_query = query.lower().replace("open", "").replace("launch", "").replace("start", "").replace("run", "").replace("app", "").strip()
         if not cleaned_query:
             return "Please specify which application to open."
         app_name = " ".join(part.capitalize() for part in cleaned_query.split())
         logging.warning(f"Extraction failed, using cleaned query '{app_name}' as target app.")

    logging.info(f"Attempting to open application: {app_name} on {sys.platform}")

    # --- Add specific app mappings here ---
    app_mappings_win = {
        "visual studio code": "code", "vscode": "code",
        "command prompt": "cmd", "cmd": "cmd",
        "file explorer": "explorer", "explorer": "explorer",
        "calculator": "calc", # Use 'calc' for broader compatibility
        "music": "spotify" # Example: map 'music' to 'spotify' on Windows
        # Add more Windows mappings
    }
    app_mappings_mac = {
        "visual studio code": "Visual Studio Code", "vscode": "Visual Studio Code",
        "terminal": "Terminal",
        "finder": "Finder",
        "calculator": "Calculator",
        "music": "Music", # Default Music app on macOS
        "camera": "Photo Booth"
        # Add more macOS mappings
    }
    app_mappings_linux = {
        "visual studio code": "code", "vscode": "code",
        "terminal": "gnome-terminal", # Example for Gnome, adjust as needed
        "files": "nautilus", # Example for Gnome file manager
        "calculator": "gnome-calculator", # Example
        "music": "rhythmbox" # Example music player
        # Add more Linux mappings (often lowercase commands)
    }
    # --- End specific app mappings ---

    try:
        if sys.platform == "win32":
            command_to_run = app_mappings_win.get(app_name.lower(), app_name) # Use mapping or original name
            subprocess.Popen(["start", "", command_to_run], shell=True)
            return f"Attempting to open {app_name}..."
        elif sys.platform == "darwin":
            command_to_run = app_mappings_mac.get(app_name.lower(), app_name) # Use mapping or original name
            subprocess.Popen(["open", "-a", command_to_run])
            return f"Attempting to open {app_name}..."
        elif sys.platform.startswith("linux"):
            command_to_run = app_mappings_linux.get(app_name.lower(), app_name.lower()) # Use mapping or lowercased name
            subprocess.Popen([command_to_run])
            return f"Attempting to open {app_name}..."
        else:
            return f"Opening applications is not supported on this OS ({sys.platform})."
    except FileNotFoundError:
         logging.error(f"Command '{command_to_run}' not found for app '{app_name}' on {sys.platform}.")
         return f"Sorry, I couldn't find or launch the application '{app_name}'. Make sure it's installed, spelled correctly, or mapped in the script."
    except Exception as e:
        logging.error(f"Error opening application {app_name}: {e}")
        return f"Sorry, I couldn't open {app_name}. Error: {e}"

def close_application(query: str) -> str:
    """
    Closes a running local application based on the user query.
    """
    app_name = extract_target(query, "app")
    if not app_name:
         # If extraction completely failed, try a simple cleanup
         cleaned_query = query.lower().replace("close", "").replace("quit", "").replace("terminate", "").replace("kill", "").replace("app", "").strip()
         if not cleaned_query:
             return "Please specify which application to close."
         app_name = " ".join(part.capitalize() for part in cleaned_query.split())
         logging.warning(f"Extraction failed, using cleaned query '{app_name}' as target app.")

    logging.info(f"Attempting to close application: {app_name} on {sys.platform}")

    # --- Add specific process name mappings here ---
    process_mappings_win = {
        "chrome": "chrome.exe",
        "notepad": "notepad.exe",
        "calculator": "calculator.exe", # Or CalculatorApp.exe
        "visual studio code": "Code.exe", "vscode": "Code.exe",
        "word": "WINWORD.EXE",
        "excel": "EXCEL.EXE",
        "powerpoint": "POWERPNT.EXE",
        "explorer": "explorer.exe", "file explorer": "explorer.exe",
        "spotify": "Spotify.exe",
        "music": "Spotify.exe" # Example: map 'music' to 'spotify' process
        # Add more Windows process names
    }
    process_mappings_mac = {
        # For Mac, osascript uses the app name, pkill might need process name or bundle ID
        "chrome": "Google Chrome", # Name for osascript/pkill -ix
        "notepad": "TextEdit", # Assuming TextEdit is the equivalent
        "calculator": "Calculator",
        "visual studio code": "Visual Studio Code", "vscode": "Visual Studio Code",
        "word": "Microsoft Word",
        "excel": "Microsoft Excel",
        "powerpoint": "Microsoft PowerPoint",
        "finder": "Finder",
        "spotify": "Spotify",
        "music": "Music",# Default Music app
        "camera": "Photo Booth"
        # Add more macOS names
    }
    process_mappings_linux = {
        # Linux process names are often lowercase
        "chrome": "chrome",
        "notepad": "gedit", # Example text editor
        "calculator": "gnome-calculator", # Example
        "visual studio code": "code", "vscode": "code",
        "word": "libreoffice-writer", # Example
        "excel": "libreoffice-calc", # Example
        "powerpoint": "libreoffice-impress", # Example
        "files": "nautilus", # Example file manager
        "spotify": "spotify",
        "music": "rhythmbox" # Example music player
        # Add more Linux process names
    }
    # --- End specific process name mappings ---

    try:
        if sys.platform == "win32":
            process_name = process_mappings_win.get(app_name.lower(), app_name + ".exe" if ' ' not in app_name and not app_name.endswith(".exe") else app_name) # Use mapping or guess .exe
            command = ["taskkill", "/F", "/IM", process_name, "/T"]
            result = subprocess.run(command, capture_output=True, text=True, check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            logging.info(f"Taskkill command: {' '.join(command)}")
            logging.info(f"Taskkill stdout: {result.stdout}")
            logging.info(f"Taskkill stderr: {result.stderr}")

            if result.returncode == 0 or "SUCCESS" in result.stdout.upper():
                return f"Attempting to close {app_name}..."
            elif "could not find" in result.stderr.lower() or "no running instance" in result.stderr.lower() or result.returncode == 128:
                 # Try UWP Calculator if standard failed
                 if app_name.lower() == "calculator" and process_name == "calculator.exe":
                     logging.info("Trying CalculatorApp.exe...")
                     command = ["taskkill", "/F", "/IM", "CalculatorApp.exe", "/T"]
                     result = subprocess.run(command, capture_output=True, text=True, check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                     if result.returncode == 0 or "SUCCESS" in result.stdout.upper():
                         return f"Attempting to close {app_name}..."
                 return f"Application '{app_name}' (process '{process_name}') not found or not running."
            else:
                error_msg = result.stderr.strip() or f"Taskkill exited with code {result.returncode}"
                return f"Failed to close {app_name}. Error: {error_msg}"

        elif sys.platform == "darwin":
            app_name_to_quit = process_mappings_mac.get(app_name.lower(), app_name) # Use mapping for osascript/pkill
            try:
                # Try graceful quit first
                script = f'quit app "{app_name_to_quit}"'
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=True, timeout=5)
                logging.info(f"osascript command: osascript -e '{script}'")
                logging.info(f"osascript stdout: {result.stdout}")
                logging.info(f"osascript stderr: {result.stderr}")
                return f"Attempting to close {app_name} gracefully..."
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                if isinstance(e, subprocess.CalledProcessError):
                    logging.warning(f"Graceful quit failed for {app_name}: {e.stderr}")
                    if "Application isn't running" in e.stderr or "Can’t get application" in e.stderr:
                         return f"Application '{app_name}' not found or not running."
                else: # TimeoutExpired
                    logging.warning(f"Graceful quit timed out for {app_name}.")

                # If graceful failed or timed out, try pkill
                logging.info(f"Trying pkill for {app_name_to_quit}.")
                command_pkill = ["pkill", "-ix", app_name_to_quit] # Case-insensitive exact name match
                result_pkill = subprocess.run(command_pkill, capture_output=True, text=True, check=False)
                logging.info(f"pkill command: {' '.join(command_pkill)}")
                logging.info(f"pkill stdout: {result_pkill.stdout}")
                logging.info(f"pkill stderr: {result_pkill.stderr}")

                if result_pkill.returncode == 0:
                     return f"Force closing {app_name}..."
                else:
                     # Check if already closed
                     check_running = subprocess.run(["pgrep", "-ix", app_name_to_quit], capture_output=True)
                     if check_running.returncode != 0:
                         return f"Application '{app_name}' not found or not running (checked with pgrep)."
                     else:
                         return f"Failed to force close {app_name}. Error: {result_pkill.stderr or 'pkill failed'}"

        elif sys.platform.startswith("linux"):
            process_name = process_mappings_linux.get(app_name.lower(), app_name.lower()) # Use mapping or lowercased name
            command_term = ["pkill", "-f", process_name] # Match command line containing the name (use with caution)
            # command_term = ["pkill", "-ix", process_name] # Alternative: Case-insensitive exact match
            result_term = subprocess.run(command_term, capture_output=True, text=True, check=False)
            logging.info(f"pkill TERM command: {' '.join(command_term)}")
            logging.info(f"pkill TERM stdout: {result_term.stdout}")
            logging.info(f"pkill TERM stderr: {result_term.stderr}")

            if result_term.returncode == 0:
                return f"Attempting to close {app_name}..."
            else:
                 check_running = subprocess.run(["pgrep", "-f", process_name], capture_output=True)
                 # check_running = subprocess.run(["pgrep", "-ix", process_name], capture_output=True) # Alternative check
                 if check_running.returncode != 0:
                     return f"Application '{app_name}' (process '{process_name}') not found or not running."
                 else:
                     return f"Failed to close {app_name}. Error: {result_term.stderr or 'pkill failed'}"
        else:
            return f"Closing applications is not supported on this OS ({sys.platform})."
    except FileNotFoundError:
         return f"Error: Required command-line tool (taskkill/osascript/pkill) not found."
    except Exception as e:
        # logging.error(f"Unexpected error closing application {app_name}: {e}")
        return f"Sorry, an unexpected error occurred while trying to close {app_name}. Error: {e}"

# --- NEW FUNCTION: Close Current Tab/Window ---
def close_current_tab_or_window() -> str:
    """
    Attempts to close the currently active tab or window using keyboard shortcuts.
    """
    try:
        logging.info("Attempting to close current tab/window.")
        if sys.platform == "win32":
            pyautogui.hotkey('ctrl', 'w') # Common shortcut for closing tab/window
            # pyautogui.hotkey('alt', 'f4') # Alternative: Closes entire active application window
        elif sys.platform == "darwin": # macOS
            pyautogui.hotkey('command', 'w') # Standard shortcut for closing tab/window
        elif sys.platform.startswith("linux"):
             pyautogui.hotkey('ctrl', 'w') # Common shortcut on Linux desktops
             # pyautogui.hotkey('alt', 'f4') # Alternative
        else:
            return "Closing tabs/windows with shortcuts is not configured for this OS."

        return "Attempting to close the current tab or window..."
    except Exception as e:
        logging.error(f"Error simulating close shortcut: {e}")
        return f"Sorry, couldn't simulate the close shortcut. Error: {e}"
    
# # --- Interactive Loop ---
# if __name__ == "__main__":
#     print("Jarvis Automation Assistant: Open/Close App or Website")
#     print("Examples:")
#     print("  open website google.com")
#     print("  open youtube")
#     print("  website open github")
#     print("  open app Notepad")
#     print("  open Calculator")
#     print("  close app Chrome")
#     print("  open music")
#     print("Type 'exit' or 'quit' to stop.")

#     while True:
#         user_cmd = input("Enter command: ").strip()
#         if not user_cmd:
#             continue
#         if user_cmd.lower() in ["exit", "quit"]:
#             print("Goodbye!")
#             break

#         user_cmd_lower = user_cmd.lower()
#         result = "Unknown command or intent." # Default result

#         # Determine intent based on keywords
#         is_open = any(word in user_cmd_lower for word in ["open", "launch", "start", "run", "visit", "go to", "browse"])
#         is_close = any(word in user_cmd_lower for word in ["close", "quit", "terminate", "kill"])
#         is_website = any(word in user_cmd_lower for word in ["website", " site", ".com", ".org", ".net", "http", "www"]) or \
#                      any(site in user_cmd_lower for site in common_sites_dict.keys()) # Check common site names
#         is_app = any(word in user_cmd_lower for word in ["app", "application"])

#         # --- Decision Logic ---
#         if is_close:
#             # Assume close always refers to an application
#             result = close_application(user_cmd)
#         elif is_open:
#             if is_website:
#                 # Clearly a website request
#                 result = open_website(user_cmd)
#             elif is_app:
#                 # Clearly an app request
#                 result = open_application(user_cmd)
#             else:
#                 # Ambiguous "open" - try app first, then website if app not found
#                 logging.info(f"Ambiguous 'open' command: '{user_cmd}'. Trying app first.")
#                 app_result = open_application(user_cmd)
#                 # Check for specific "not found" or "specify" errors before falling back
#                 if ("not found" in app_result.lower() or \
#                     "couldn't find or launch" in app_result.lower() or \
#                     "please specify" in app_result.lower()):
#                     logging.info(f"App open failed or ambiguous ('{app_result}'). Trying website/search.")
#                     website_result = open_website(user_cmd)
#                     # Combine results meaningfully
#                     if "please specify" in app_result.lower() and "please specify" in website_result.lower():
#                          result = "Please specify what application or website you want to open."
#                     elif "please specify" in app_result.lower():
#                          result = website_result # If app failed due to lack of specification, trust website result
#                     else:
#                          result = f"App not found. {website_result}" # App specifically not found, report website attempt
#                 else:
#                     result = app_result # App likely opened or had a different error
#         else:
#              # If no clear open/close action, maybe it's an implicit open? Treat as ambiguous.
#              logging.info(f"No clear action verb found in '{user_cmd}'. Treating as ambiguous open.")
#              app_result = open_application("open " + user_cmd) # Add "open" for clarity to function
#              if ("not found" in app_result.lower() or \
#                  "couldn't find or launch" in app_result.lower() or \
#                  "please specify" in app_result.lower()):
#                  logging.info(f"Implicit app open failed ('{app_result}'). Trying website/search.")
#                  website_result = open_website("open " + user_cmd)
#                  if "please specify" in app_result.lower() and "please specify" in website_result.lower():
#                       result = "Please specify what application or website you want to open."
#                  elif "please specify" in app_result.lower():
#                       result = website_result
#                  else:
#                       result = f"App not found. {website_result}"
#              else:
#                  result = app_result


#         print(f"-> {result}")
