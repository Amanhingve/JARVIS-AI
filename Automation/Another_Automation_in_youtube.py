import pyautogui
import platform

# Check OS
IS_MACOS = platform.system() == 'Darwin'
IS_WINDOWS = platform.system() == 'Windows'

# --- Video Pan Controls ---
def pan_up():
    pyautogui.press('w')

def pan_down():
    pyautogui.press('s')

def pan_left():
    pyautogui.press('a')

def pan_right():
    pyautogui.press('d')

# --- Zoom Controls ---
def zoom_in():
    if IS_MACOS:
        pyautogui.hotkey('command', '+')
    else:
        pyautogui.press('+')

def zoom_out():
    if IS_MACOS:
        pyautogui.hotkey('command', '-')
    else:
        pyautogui.press('-')

# --- Common Media Controls ---
def go_to_search_box():
    pyautogui.press('/')

def toggle_play_pause():
    pyautogui.press('k')

def toggle_mute_unmute():
    pyautogui.press('m')

def toggle_full_screen():
    pyautogui.press('f')

def toggle_theater_mode():
    pyautogui.press('t')

def toggle_miniplayer_mode():
    pyautogui.press('i')

def exit_full_screen():
    pyautogui.press('esc')

def toggle_party_mode():
    pyautogui.write('awesome')

# --- Navigation Controls ---
def navigate_forward():
    pyautogui.press('tab')

def navigate_backward():
    pyautogui.hotkey('shift', 'tab')
