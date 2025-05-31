# /Users/amanhingve/Program/Amanpython/PROJECT/Ai_project/Automation/pen_drive_plug_check.py
import os
import sys
import psutil
import time
import random
import platform
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the project root to sys.path
if project_root not in sys.path: # Avoid adding duplicates
    sys.path.insert(0, project_root)

try:
    from Data.DLG import pen_drive_connect, pen_drive_disconnect
    from ENGINE.TTS.TTS_DF import speak
    dialog_available = True
except ImportError:
    # Define dummy lists/functions if imports fail
    pen_drive_connect = ["Pen drive connected."]
    pen_drive_disconnect = ["Pen drive disconnected."]
    def speak(text): print(f"TTS (speak): {text}")
    dialog_available = False
    logging.warning("Could not import DLG or TTS modules for pen_drive_plug_check.")


def get_usb_devices():
    """
    Returns a set of removable USB drive paths across Windows, Mac, and Linux.
    """
    system_os = platform.system()
    devices = set() # Initialize empty set

    try:
        if system_os == "Windows":
            # Use wmic for potentially more reliable removable check
            try:
                output = subprocess.check_output(['wmic', 'logicaldisk', 'where', 'drivetype=2', 'get', 'deviceid'], text=True)
                # wmic output might have extra lines/spaces
                devices = {line.strip() + '\\' for line in output.splitlines() if ':' in line}
                logging.debug(f"WMIC detected removable drives: {devices}")
            except (subprocess.CalledProcessError, FileNotFoundError) as e_wmic:
                logging.warning(f"WMIC failed ({e_wmic}), falling back to psutil for removable drives.")
                # Fallback using psutil
                devices = {disk.device for disk in psutil.disk_partitions(all=True) if 'removable' in disk.opts or disk.fstype == ''} # Added fstype check

        elif system_os == "Darwin":  # MacOS
            # Using diskutil list external physical might be too broad (includes external HDDs)
            # Let's try listing volumes under /Volumes and checking if they are removable
            # This is heuristic and might need refinement
            volumes_path = "/Volumes"
            potential_drives = set()
            if os.path.exists(volumes_path):
                for item in os.listdir(volumes_path):
                    full_path = os.path.join(volumes_path, item)
                    # Basic check: ignore system volumes, check if it's a mount point
                    # and potentially if it's not the main startup disk
                    if os.path.ismount(full_path) and item not in ["Macintosh HD", "Recovery", "Preboot", "VM"]:
                         # Further check if possible (e.g., using diskutil info) - complex
                         # For simplicity, assume mounted non-system volumes might be USB
                         potential_drives.add(full_path)
            devices = potential_drives # Use the found volumes
            logging.debug(f"macOS heuristic detected potential USB volumes: {devices}")
            # Alternative using diskutil (might be better but needs parsing)
            # try:
            #     output = subprocess.check_output(['diskutil', 'list', 'external'], text=True)
            #     # Parse output to find mount points associated with external disks
            #     # ... complex parsing logic ...
            # except (subprocess.CalledProcessError, FileNotFoundError):
            #     logging.warning("diskutil list external failed.")


        elif system_os == "Linux":
            # Using lsblk is generally good
            try:
                # Get mount points for removable devices
                output = subprocess.check_output(['lsblk', '-o', 'MOUNTPOINT,RM', '-n', '-p'], text=True)
                devices = {line.split()[0] for line in output.splitlines() if len(line.split()) > 1 and line.split()[1] == '1'}
                logging.debug(f"lsblk detected removable drive mount points: {devices}")
            except (subprocess.CalledProcessError, FileNotFoundError) as e_lsblk:
                 logging.warning(f"lsblk failed ({e_lsblk}), cannot reliably detect USB drives on Linux.")

        else:
            logging.warning(f"Unsupported operating system for USB check: {system_os}")

    except Exception as e:
        logging.error(f"Error getting USB devices on {system_os}: {e}", exc_info=True)

    # Filter out empty strings just in case
    return {d for d in devices if d}


# --- NEW FUNCTION for one-time check ---
def is_pen_drive_present():
    """
    Checks if any removable USB drive is currently connected.
    Returns a user-friendly string indicating the status.
    """
    logging.info("Performing one-time check for pen drives...")
    current_devices = get_usb_devices()
    if current_devices:
        # Create a more readable list for the user
        device_names = [os.path.basename(d.rstrip('\\/')) for d in current_devices] # Get drive letter/volume name
        logging.info(f"Pen drive(s) detected: {current_devices}")
        return f"Yes, I detect {len(current_devices)} pen drive(s) connected: {', '.join(device_names)}."
    else:
        logging.info("No pen drives detected.")
        return "No, I don't detect any pen drives connected right now."
# --- END NEW FUNCTION ---


# --- Monitoring functions (Keep if used elsewhere, otherwise optional) ---
previous_devices_monitor = set() # Use a different variable for the monitor

def pen_drive_connected():
    """
    Monitors USB devices for connection/disconnection and provides feedback.
    (This runs in a loop and is NOT suitable for direct function calling)
    """
    global previous_devices_monitor
    previous_devices_monitor = get_usb_devices() # Initialize monitor state
    logging.info("Starting continuous pen drive monitoring...")

    try:
        while True:
            current_devices = get_usb_devices()

            added = current_devices - previous_devices_monitor
            removed = previous_devices_monitor - current_devices

            if added:
                for device in added:
                    if dialog_available:
                        random_connect_msg = random.choice(pen_drive_connect)
                        speak(random_connect_msg)
                    logging.info(f"Pen drive connected: {device}")

            if removed:
                for device in removed:
                    if dialog_available:
                        random_disconnect_msg = random.choice(pen_drive_disconnect)
                        speak(random_disconnect_msg)
                    logging.info(f"Pen drive disconnected: {device}")

            previous_devices_monitor = current_devices
            time.sleep(5) # Check interval

    except KeyboardInterrupt:
        logging.info("Pen drive connection monitoring stopped.")
    except Exception as e:
        logging.error(f"An error occurred in pen_drive_connected monitoring: {e}", exc_info=True)


# --- Old pen_drive_connected1 (Likely redundant now) ---
# def pen_drive_connected1():
#     global previous_devices # Relied on a potentially stale global state
#     current_devices = get_usb_devices()
#     added = current_devices - previous_devices
#     if added:
#         # ... speak connect ...
#     else:
#         # ... speak disconnect (misleading) ...
#     previous_devices = current_devices


# Example usage for testing the new function:
if __name__ == "__main__":
    print("Testing is_pen_drive_present():")
    status_message = is_pen_drive_present()
    print(status_message)

    # To test the monitoring function (runs indefinitely):
    # print("\nStarting monitoring (Press Ctrl+C to stop)...")
    # pen_drive_connected()
