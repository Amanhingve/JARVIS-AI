import pyautogui
import platform

# Check OS
IS_MACOS = platform.system() == 'Darwin'
IS_WINDOWS = platform.system() == 'Windows'

def open_new_tab():
    if IS_WINDOWS:
        pyautogui.hotkey('ctrl', 't') 
    elif IS_MACOS:
        pyautogui.hotkey('command', 't')  
    # pyautogui.hotkey('command','t' if IS_MACOS else 'ctrl', 't')

def close_tab():
    if IS_WINDOWS:
        pyautogui.hotkey('ctrl', 'w')  
    elif IS_MACOS:
        pyautogui.hotkey('command', 'w')  
    # pyautogui.hotkey('command','w' if IS_MACOS else 'ctrl', 'w')

def open_browser_menu():
    if IS_WINDOWS:
        pyautogui.hotkey('alt', 'f')  # Alt+F opens menu on Windows
    elif IS_MACOS:
        pyautogui.hotkey('command', ',')  # Cmd+, often opens Preferences

def zoom_in():
    pyautogui.hotkey('command' if IS_MACOS else 'ctrl', '+')

def zoom_out():
    pyautogui.hotkey('command' if IS_MACOS else 'ctrl', '-')

def refresh_page():
    pyautogui.hotkey('command' if IS_MACOS else 'ctrl', 'r')

def switch_to_next_tab():
    pyautogui.hotkey('command' if IS_MACOS else 'ctrl', 'tab')

def switch_to_previous_tab():
    if IS_MACOS:
        pyautogui.hotkey('command', 'shift', 'tab')
    else:
        pyautogui.hotkey('ctrl', 'shift', 'tab')

def open_history():
    pyautogui.hotkey('command' if IS_MACOS else 'ctrl', 'h')

def open_bookmarks():
    pyautogui.hotkey('command' if IS_MACOS else 'ctrl', 'b')

def go_back():
    pyautogui.hotkey('command' if IS_MACOS else 'alt', 'left')

def go_forward():
    pyautogui.hotkey('command' if IS_MACOS else 'alt', 'right')

def open_dev_tools():
    pyautogui.hotkey('command' if IS_MACOS else 'ctrl', 'option' if IS_MACOS else 'shift', 'i')

def toggle_full_screen():
    if IS_MACOS:
        pyautogui.hotkey('control', 'command', 'f')  # Standard macOS fullscreen shortcut
    else:
        pyautogui.hotkey('f11')

def open_private_window():
    pyautogui.hotkey('command' if IS_MACOS else 'ctrl', 'shift', 'n')
