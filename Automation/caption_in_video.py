# /Users/amanhingve/Program/Amanpython/PROJECT/Ai_project/Automation/caption_in_video.py
import pyautogui
import sys
import os
import time
import platform

# --- Add project root to sys.path ---
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- End path modification ---

from ENGINE.STT.fast_stt import speech_to_text

# Check OS
IS_MACOS = platform.system() == 'Darwin'
IS_WINDOWS = platform.system() == 'Windows'

# Configure pyautogui for macOS
pyautogui.PAUSE = 0.1

# --- Volume Control ---
def volume_up():
    if IS_MACOS:
        os.system("osascript -e 'set volume output volume ((output volume of (get volume settings)) + 10)'")
    elif IS_WINDOWS:
        pyautogui.press('volumeup')

def volume_down():
    if IS_MACOS:
        os.system("osascript -e 'set volume output volume ((output volume of (get volume settings)) - 10)'")
    elif IS_WINDOWS:
        pyautogui.press('volumedown')

def mute_volume():
    if IS_MACOS:
        os.system("osascript -e 'set volume with output muted'")
    elif IS_WINDOWS:
        pyautogui.press('volumemute')

def unmute_volume():
    if IS_MACOS:
        os.system("osascript -e 'set volume without output muted'")
    elif IS_WINDOWS:
        pyautogui.press('volumemute')  # Toggle mute again to unmute

# --- Basic Seeking ---
def seek_forward():
    pyautogui.press('right')

def seek_backward():
    pyautogui.press('left')

def seek_forward_10s():
    pyautogui.press('l')

def seek_backward_10s():
    pyautogui.press('j')

# --- Frame Seeking ---
def seek_backward_frame():
    pyautogui.press(',')

def seek_forward_frame():
    pyautogui.press('.')

# --- Position Seeking ---
def seek_to_beginning():
    if IS_MACOS:
        pyautogui.hotkey('command', 'left')
    elif IS_WINDOWS:
        pyautogui.press('home')

def seek_to_end():
    if IS_MACOS:
        pyautogui.hotkey('command', 'right')
    elif IS_WINDOWS:
        pyautogui.press('end')

# --- Chapter Navigation ---
def seek_to_previous_chapter():
    if IS_MACOS:
        pyautogui.hotkey('command', 'left')
    elif IS_WINDOWS:
        pyautogui.hotkey('ctrl', 'left')

def seek_to_next_chapter():
    if IS_MACOS:
        pyautogui.hotkey('command', 'right')
    elif IS_WINDOWS:
        pyautogui.hotkey('ctrl', 'right')

# --- Playlist Navigation ---
def move_to_next_video():
    pyautogui.press('n')

def move_to_previous_video():
    pyautogui.press('p')

# --- Playback Speed ---
def decrease_playback_speed():
    pyautogui.press('[')

def increase_playback_speed():
    pyautogui.press(']')

# --- Subtitles / Appearance ---
def toggle_subtitles():
    pyautogui.press('c')

def increase_font_size():
    if IS_MACOS:
        pyautogui.hotkey('shift', '=')
    elif IS_WINDOWS:
        pyautogui.press('+')

def decrease_font_size():
    pyautogui.press('-')

def rotate_text_opacity():
    pyautogui.press('o')

def rotate_window_opacity():
    pyautogui.press('w')


# --- Main function for direct testing (Optional) ---
# def main():
#     print(f"Video Control Test Mode on {'macOS' if IS_MACOS else 'Windows/Linux'}. Press Ctrl+C to exit.")
#     print("Commands: volume up, volume down, seek forward, seek backward, seek forward 10s, seek backward 10s,")
#     print("          seek beginning, seek end, prev chapter, next chapter, decrease speed, increase speed,")
#     print("          next video, prev video, toggle subtitles, ... (and others)")
    
#     try:
#         while True:
#             # For testing, you can uncomment this line to use keyboard input instead of speech
#             command = input("Enter command: ").lower().strip()
            
#             # Fixed the typo: changed .lover() to .lower()
#             # command = speech_to_text().lower()
            
#             if command == "volume up": volume_up()
#             elif command == "volume down": volume_down()
#             elif command == "seek forward": seek_forward()
#             elif command == "seek backward": seek_backward()
#             elif command == "seek forward 10s": seek_forward_10s()
#             elif command == "seek backward 10s": seek_backward_10s()
#             elif command == "seek backward frame": seek_backward_frame()
#             elif command == "seek forward frame": seek_forward_frame()
#             elif command == "seek beginning" or command == "seek to beginning": seek_to_beginning()
#             elif command == "seek end" or command == "seek to end": seek_to_end()
#             elif command == "prev chapter" or command == "seek to previous chapter": seek_to_previous_chapter()
#             elif command == "next chapter" or command == "seek to next chapter": seek_to_next_chapter()
#             elif command == "decrease speed" or command == "decrease playback speed": decrease_playback_speed()
#             elif command == "increase speed" or command == "increase playback speed": increase_playback_speed()
#             elif command == "next video" or command == "move to next video": move_to_next_video()
#             elif command == "prev video" or command == "move to previous video": move_to_previous_video()
#             elif command == "toggle subtitles" or  command == "toggle subtitle" or command == "subtitle on" or command == "subtitle of": toggle_subtitles()
#             elif command == "increase font" or command == "increase font size": increase_font_size()
#             elif command == "decrease font" or command == "decrease font size": decrease_font_size()
#             elif command == "text opacity" or command == "rotate text opacity": rotate_text_opacity()
#             elif command == "window opacity" or command == "rotate window opacity": rotate_window_opacity()
#             elif command in ["exit", "quit"]: break
#             else: print("Invalid command")
#             print(f"Executed: {command}")

#     except KeyboardInterrupt:
#         print("\nExiting test mode.")
#     except Exception as e:
#         print(f"Error: {e}")

# if __name__ == "__main__":
#     main()
