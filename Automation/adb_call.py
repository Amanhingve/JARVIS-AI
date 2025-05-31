# Automation/adb_call.py

from math import e
import subprocess
import logging
import platform
import shlex
import sys
import re
import csv
import os
import time # <-- ADDED for sleep
import xml.etree.ElementTree as ET
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the path to the contacts file relative to this script
CONTACT_FILE_NAME = "Data/local_contacts.csv"
AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
# Corrected path joining: Join with the directory the script is in
CONTACT_FILE_PATH = os.path.join(CONTACT_FILE_NAME) # <-- CORRECTED PATH

# Default ADB port for TCP/IP
ADB_WIFI_PORT = 5555

last_known_wifi_adb_address = None

# --- run_adb_command function (Keep As Is, but ensure it handles -s flag if needed) ---
def run_adb_command(command_args, device_id=None):
    """Helper function to run ADB commands, optionally targeting a specific device."""
    if platform.system() == 'Windows':
        adb_executable = "adb"
    else: # macOS or Linux
        adb_executable = "adb"

    # Prepend device target if specified
    if device_id:
        full_command = [adb_executable, "-s", device_id] + command_args
    else:
        full_command = [adb_executable] + command_args

    logging.info(f"Running ADB command: {' '.join(shlex.quote(str(arg)) for arg in full_command)}")

    try:
        string_command = [str(arg) for arg in full_command]
        result = subprocess.run(string_command, capture_output=True, text=True, check=False, timeout=25)

        stdout_lower = result.stdout.lower() if result.stdout else ""
        stderr_lower = result.stderr.lower() if result.stderr else ""
        combined_output_lower = stdout_lower + stderr_lower

        # --- Error Detection (Simplified for brevity, keep your previous robust checks) ---
        error_output_for_check = result.stderr.strip() if result.stderr else result.stdout.strip()
        error_output_lower_for_check = error_output_for_check.lower()

        if "unauthorized" in error_output_lower_for_check:
             error_msg = "Device unauthorized. Please check the prompt on your Android phone and allow USB debugging."
             logging.error(f"ADB command failed: {error_msg}")
             return False, error_msg
        elif "offline" in error_output_lower_for_check:
             error_msg = "Device offline. Please ensure it's connected properly and awake."
             logging.error(f"ADB command failed: {error_msg}")
             return False, error_msg
        elif ("device" in error_output_lower_for_check and "not found" in error_output_lower_for_check) or "no devices/emulators found" in error_output_lower_for_check:
             if "devices" in full_command and "list of devices attached" in stdout_lower and len(result.stdout.strip().splitlines()) <= 1:
                 error_msg = "No device found. Ensure it's connected, USB debugging is enabled, and authorized."
             else:
                 error_msg = "Device not found. Ensure it's connected, USB debugging is enabled, and authorized."
             logging.error(f"ADB command failed: {error_msg}")
             return False, error_msg
        # --- End Simplified Error Detection ---

        if result.returncode == 0:
            logging.info(f"ADB command successful (RC=0). Output:\n{result.stdout.strip()}")
            return True, result.stdout.strip()
        else:
            error_output = result.stderr.strip() if result.stderr else result.stdout.strip()
            if not error_output: error_output = f"ADB command failed with return code {result.returncode}"
            logging.error(f"ADB command failed. Return code: {result.returncode}. Error:\n{error_output}")
            return False, f"Error: ADB command failed (RC={result.returncode}). Details: {error_output}"

    except FileNotFoundError:
        logging.error("ADB command failed: 'adb' executable not found.")
        return False, "Error: 'adb' command not found. Install Android Platform Tools and ensure it's in PATH."
    except subprocess.TimeoutExpired:
        logging.error("ADB command timed out.")
        return False, "Error: ADB command timed out."
    except Exception as e:
        logging.error(f"An unexpected error occurred running ADB command: {e}", exc_info=True)
        return False, f"An unexpected error occurred: {e}"

# --- MODIFIED FUNCTION: Check ADB Server and Device Connection ---
def check_adb_connection():
    """
    Checks ADB server and lists connected devices.
    Returns:
        tuple: (bool: success, list: devices_list, str: error_message)
               devices_list contains tuples of (device_id, status, connection_type)
               connection_type is 'usb', 'wifi', or 'unknown'
    """
    # 1. Ensure ADB server is running
    logging.info("Checking/Starting ADB server...")
    server_success, server_output = run_adb_command(["start-server"])
    if not server_success:
        if "'adb' command not found" in server_output:
             return False, [], f"ADB Error: {server_output}"
        else:
             return False, [], f"Failed to start or connect to ADB server: {server_output}"

    # 2. Check ADB device connection
    logging.info("Checking ADB device connections...")
    connect_success, connect_output = run_adb_command(["devices"])
    if not connect_success:
        # Don't treat "no devices found" as an error here, just return empty list
        if "no device" in connect_output.lower() or "not found" in connect_output.lower():
             logging.info("No devices/emulators found via 'adb devices'.")
             return True, [], "" # Command ran, but no devices listed
        else:
             return False, [], f"ADB Connection Error: {connect_output}" # Actual error running command

    lines = connect_output.strip().splitlines()
    devices_found = []
    if len(lines) > 1: # More than just "List of devices attached"
        for line in lines[1:]:
            parts = line.strip().split('\t')
            if len(parts) == 2:
                device_id = parts[0]
                status = parts[1].lower()
                # Determine connection type based on device_id format
                if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+', device_id):
                    conn_type = 'wifi'
                elif ':' not in device_id: # Basic check for USB/Emulator ID
                    conn_type = 'usb' # Treat emulators and USB devices similarly here
                else:
                    conn_type = 'unknown'
                devices_found.append((device_id, status, conn_type))
                logging.info(f"Found device: {device_id}, Status: {status}, Type: {conn_type}")

    return True, devices_found, ""

# --- NEW FUNCTION: Get Device IP Address ---
def get_device_ip(device_id):
    """Gets the Wi-Fi IP address of the specified device."""
    logging.info(f"Attempting to get IP address for device {device_id}...")
    # Try common commands to get IP address
    # Using 'ip addr show wlan0' is often reliable for Wi-Fi
    cmd_args = ["shell", "ip", "addr", "show", "wlan0"]
    success, output = run_adb_command(cmd_args, device_id=device_id)

    if success and output:
        # Search for inet address in the output
        match = re.search(r'inet (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/', output)
        if match:
            ip_address = match.group(1)
            logging.info(f"Found IP address for {device_id}: {ip_address}")
            return ip_address
        else:
            logging.warning(f"Could not parse IP address from 'ip addr show wlan0' output for {device_id}.")
    else:
        logging.warning(f"Failed to execute 'ip addr show wlan0' on {device_id}. Trying 'ip route'.")

    # Fallback: Try 'ip route'
    cmd_args = ["shell", "ip", "route"]
    success, output = run_adb_command(cmd_args, device_id=device_id)
    if success and output:
         # Look for lines with wlan and src
         for line in output.splitlines():
              if 'wlan' in line and 'src' in line:
                   match = re.search(r'src (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', line)
                   if match:
                        ip_address = match.group(1)
                        logging.info(f"Found IP address via 'ip route' for {device_id}: {ip_address}")
                        return ip_address
         logging.warning(f"Could not parse IP address from 'ip route' output for {device_id}.")
    else:
         logging.warning(f"Failed to execute 'ip route' on {device_id}.")


    logging.error(f"Could not determine IP address for device {device_id}.")
    return None

# --- NEW FUNCTION: Connect ADB over Wi-Fi ---
def connect_adb_wifi(usb_device_id):
    """Attempts to switch the given USB device to Wi-Fi ADB and connect."""
    # global last_known_wifi_adb_address # <-- ADDED global variable
    print(f"Attempting to enable Wi-Fi ADB for device {usb_device_id}...")

    ip_address = get_device_ip(usb_device_id)
    if not ip_address:
        print(f"Error: Could not get IP address for {usb_device_id}. Ensure Wi-Fi is enabled on the device.")
        # last_known_wifi_adb_address = None # Reset last known address
        return False, None # Indicate failure

    # Enable TCP/IP mode on the device
    print(f"Enabling TCP/IP mode on port {ADB_WIFI_PORT} for {usb_device_id}...")
    tcpip_success, tcpip_output = run_adb_command(["tcpip", str(ADB_WIFI_PORT)], device_id=usb_device_id)

    if not tcpip_success:
        print(f"Error: Failed to set device {usb_device_id} to TCP/IP mode. Output: {tcpip_output}")
        # Check for common reason: already in tcpip mode (might still work)
        if "already in TCP mode" in tcpip_output:
             print("Device may already be in TCP/IP mode. Proceeding with connection attempt...")
        else:
             return False, None # Indicate failure

    # Wait a moment for the adb daemon on the device to restart
    print("Waiting a few seconds for device ADB to restart...")
    time.sleep(10) # Adjust sleep time if needed

    # Connect to the device over Wi-Fi
    wifi_device_addr = f"{ip_address}:{ADB_WIFI_PORT}"
    print(f"Attempting to connect to {wifi_device_addr}...")
    connect_success, connect_output = run_adb_command(["connect", wifi_device_addr])

    if connect_success and ("connected to" in connect_output.lower() or "already connected" in connect_output.lower()):
        print(f"Successfully connected to device via Wi-Fi: {wifi_device_addr}")
        # Verify connection with adb devices again
        verify_success, devices_list, _ = check_adb_connection()
        if verify_success:
             for dev_id, status, _ in devices_list:
                  if dev_id == wifi_device_addr and status == 'device':
                       print("Wi-Fi connection confirmed.")
                       return True, wifi_device_addr # Indicate success and return Wi-Fi ID
        # If verification fails or connect command output was ambiguous
        print(f"Warning: Connection command reported success, but verification failed or was unclear. Output: {connect_output}")
        # Still might be connected, return True but let later steps confirm
        return True, wifi_device_addr

    else:
        print(f"Error: Failed to connect to device via Wi-Fi at {wifi_device_addr}.")
        print(f"ADB connect output: {connect_output}")
        # Try disconnecting first, in case of stale connection
        print(f"Attempting to disconnect {wifi_device_addr} and retry...")
        run_adb_command(["disconnect", wifi_device_addr])
        time.sleep(1)
        connect_success, connect_output = run_adb_command(["connect", wifi_device_addr])
        if connect_success and ("connected to" in connect_output.lower() or "already connected" in connect_output.lower()):
             print(f"Successfully connected to device via Wi-Fi after retry: {wifi_device_addr}")
             return True, wifi_device_addr
        else:
             print(f"Error: Still failed to connect to {wifi_device_addr} after retry.")
             return False, None # Indicate failure

def ensure_adb_connection():
    """
    Ensures an authorized ADB device is connected, preferring Wi-Fi.
    Attempts to switch from USB to Wi-Fi if necessary.
    Attempts to reconnect to the last known Wi-Fi address if disconnected.

    Returns:
        tuple: (device_id, error_message)
               device_id is the ID of the authorized device (str) or None if failed.
               error_message is None on success, or an error string on failure.
    """
    global last_known_wifi_adb_address
    logging.info("Ensuring ADB connection...")

    # 1. Initial Check
    check_ok, devices, error_msg = check_adb_connection()
    if not check_ok:
        logging.error(f"Initial ADB check failed: {error_msg}")
        return None, error_msg

    authorized_wifi_device = None
    authorized_usb_candidate = None

    # Find the first authorized device (prefer Wi-Fi)
    for dev_id, status, conn_type in devices:
        if status == 'device':
            if conn_type == 'wifi':
                authorized_wifi_device = dev_id
                logging.info(f"Found existing authorized Wi-Fi device: {authorized_wifi_device}")
                # Update last known address just in case
                last_known_wifi_adb_address = authorized_wifi_device
                return authorized_wifi_device, None # Use existing Wi-Fi
            elif conn_type == 'usb' and not authorized_usb_candidate: # Only store the first USB candidate
                authorized_usb_candidate = dev_id
                logging.info(f"Found authorized USB device candidate: {authorized_usb_candidate}")
            elif conn_type == 'unknown' and not authorized_wifi_device and not authorized_usb_candidate:
                 logging.warning(f"Found authorized device with unknown connection type: {dev_id}. Treating as potential USB.")
                 authorized_usb_candidate = dev_id # Treat unknown as USB for potential switch

        elif status == 'unauthorized':
            logging.warning(f"Found unauthorized device: {dev_id}. Please allow USB debugging on the device.")
        elif status == 'offline':
            logging.warning(f"Found offline device: {dev_id}. Please check connection.")

    # 2. Attempt Wi-Fi Switch if only USB found
    if not authorized_wifi_device and authorized_usb_candidate:
        logging.info(f"No Wi-Fi device found. Attempting to switch USB device {authorized_usb_candidate} to Wi-Fi...")
        wifi_success, wifi_device_addr = connect_adb_wifi(authorized_usb_candidate)
        if wifi_success:
            logging.info(f"Successfully switched to and connected via Wi-Fi: {wifi_device_addr}")
            return wifi_device_addr, None # Use the new Wi-Fi connection
        else:
            logging.warning("Failed to switch to Wi-Fi ADB. Falling back to USB connection.")
            # Fallback to the USB device if switch failed
            return authorized_usb_candidate, None

    # 3. Attempt Reconnect if No Device Found but Last Known Wi-Fi Exists
    if not authorized_wifi_device and not authorized_usb_candidate:
        if last_known_wifi_adb_address:
            logging.warning("No authorized device found. Attempting to reconnect to last known Wi-Fi address...")
            print(f"Attempting to reconnect to {last_known_wifi_adb_address}...")
            connect_success, connect_output = run_adb_command(["connect", last_known_wifi_adb_address])

            if connect_success and ("connected to" in connect_output.lower() or "already connected" in connect_output.lower()):
                logging.info(f"Successfully reconnected to {last_known_wifi_adb_address}.")
                time.sleep(1) # Short pause

                # Verify connection again
                check_ok_retry, devices_retry, error_msg_retry = check_adb_connection()
                if check_ok_retry:
                    reconnected_device = next((d for d in devices_retry if d[0] == last_known_wifi_adb_address and d[1] == 'device'), None)
                    if reconnected_device:
                        logging.info(f"Confirmed authorized Wi-Fi device after reconnect: {last_known_wifi_adb_address}")
                        return last_known_wifi_adb_address, None
                    else:
                        logging.error(f"Reconnect command succeeded, but device {last_known_wifi_adb_address} not listed as authorized afterwards.")
                        # Fall through to the final error
                else:
                    logging.error(f"Failed to check devices after reconnect attempt: {error_msg_retry}")
                    # Fall through to the final error
            else:
                logging.error(f"Failed to reconnect to {last_known_wifi_adb_address}. Output: {connect_output}")
                # Optionally try disconnecting first: run_adb_command(["disconnect", last_known_wifi_adb_address])
                # Fall through to the final error
        else:
             logging.info("No authorized device found and no previous Wi-Fi address known.")


    # 4. Final Check and Error
    if authorized_wifi_device: # Should have been returned earlier, but double-check
        return authorized_wifi_device, None
    if authorized_usb_candidate: # Should have been returned earlier (fallback), but double-check
        return authorized_usb_candidate, None

    # If we reach here, no authorized device could be found or connected
    final_error_msg = "No authorized ADB device found. Connect device (USB recommended for initial setup), enable USB debugging, and authorize."
    logging.error(final_error_msg)
    return None, final_error_msg
# --- END NEW FUNCTION ---

# --- Function to Search Contacts in Local CSV File (Keep As Is) ---
def get_contact_number_from_file(name_query: str):
    """Searches the local CSV file for a contact name (case-insensitive partial match)
       and returns the selected phone number."""

    found_contacts = []
    try:
        # Use the corrected CONTACT_FILE_PATH
        logging.info(f"Searching for '{name_query}' in '{CONTACT_FILE_PATH}' (case-insensitive)...")
        with open(CONTACT_FILE_PATH, mode='r', encoding='utf-8', newline='') as csvfile:
            # Use DictReader to easily access columns by header name ('Name', 'Number')
            reader = csv.DictReader(csvfile)
            if 'Name' not in reader.fieldnames or 'Number' not in reader.fieldnames:
                 logging.error(f"CSV file '{CONTACT_FILE_PATH}' must contain 'Name' and 'Number' columns in the header.")
                 return None, f"Error: The contact file '{CONTACT_FILE_NAME}' is missing the required 'Name' or 'Number' header."

            for row in reader:
                contact_name = row.get('Name', '').strip()
                contact_number = row.get('Number', '').strip()

                # Perform case-insensitive partial match
                if contact_name and contact_number and name_query.lower() in contact_name.lower():
                    # Store as (name, number) tuple
                    if (contact_name, contact_number) not in found_contacts:
                        found_contacts.append((contact_name, contact_number))
                        logging.debug(f"Found potential match: Name='{contact_name}', Number='{contact_number}'")

    except FileNotFoundError:
        logging.error(f"Contact file not found at '{CONTACT_FILE_PATH}'. Please create '{CONTACT_FILE_NAME}' in the '{os.path.basename(AUTOMATION_DIR)}/Data' folder.")
        # Provide a clearer path hint
        return None, f"Error: Contact file '{CONTACT_FILE_NAME}' not found in the 'Data' subfolder. Please create it at: {CONTACT_FILE_PATH}"
    except Exception as e:
        logging.error(f"Error reading contact file '{CONTACT_FILE_PATH}': {e}", exc_info=True)
        return None, f"Error reading contact file: {e}"

    # --- Handle Search Results ---
    if not found_contacts:
        logging.info(f"No contact found matching '{name_query}' in '{CONTACT_FILE_NAME}'.")
        return None, f"Sorry, I couldn't find a contact matching '{name_query}' in '{CONTACT_FILE_NAME}'."

    if len(found_contacts) == 1:
        name, number = found_contacts[0]
        logging.info(f"Found unique contact in file: {name} - {number}")
        return number, f"Found number {number} for {name} in '{CONTACT_FILE_NAME}'."
    else:
        # Multiple matches, ask user
        print(f"\nFound multiple matching contacts in '{CONTACT_FILE_NAME}':")
        for i, (name, number) in enumerate(found_contacts):
            print(f"  {i + 1}: {name} - {number}")
        while True:
            try:
                choice = input(f"Which one do you want to call? (Enter number 1-{len(found_contacts)}): ")
                index = int(choice) - 1
                if 0 <= index < len(found_contacts):
                    selected_name, selected_number = found_contacts[index]
                    logging.info(f"User selected: {selected_name} - {selected_number}")
                    return selected_number, f"Using number {selected_number} for {selected_name}."
                else:
                    print("Invalid choice. Please enter a number from the list.")
            except ValueError:
                print("Invalid input. Please enter a number.")

def mask_phone_number(number_str):
    """Masks a phone number, showing only prefix, first 2, and last 2 digits."""
    if not number_str:
        return ""

    prefix = ""
    digits_part = number_str

    # Separate prefix (like +91) if present
    if number_str.startswith('+'):
        # Find the first sequence of digits after '+'
        match = re.match(r'(\+\d+)(\d.*)', number_str)
        if match:
            prefix = match.group(1) # e.g., +91
            digits_part = match.group(2) # The rest of the digits
        else: # Handle cases like just '+' (unlikely for valid numbers)
            prefix = "+"
            digits_part = number_str[1:]
    
    # Ensure we are working only with digits for the main part
    digits_only = ''.join(filter(str.isdigit, digits_part))
    length = len(digits_only)

    if length <= 4:
        # If 4 or fewer digits after prefix, mask them all
        return prefix + "*" * length
    else:
        first_two = digits_only[:2]
        last_two = digits_only[-2:]
        # Calculate number of asterisks needed
        num_asterisks = length - 4
        asterisks = "*" * num_asterisks
        return f"{prefix}{first_two}{asterisks}{last_two}"

# --- make_phone_call_adb function (MODIFIED to accept device_id) ---
def make_phone_call_adb(recipient_number: str, sim_slot: int = None, target_device_id: str = None):
    """
    Attempts to initiate a phone call on a connected Android device using ADB,
    optionally trying to specify a SIM slot and targeting a specific device.
    """
    if not recipient_number:
        return "Error: Please provide a phone number to call."

    # --- Number cleaning (Keep As Is) ---
    cleaned_number = recipient_number.strip()
    has_plus = cleaned_number.startswith('+')
    cleaned_number_digits = ''.join(filter(str.isdigit, cleaned_number))
    if has_plus: final_cleaned_number = '+' + cleaned_number_digits
    else: final_cleaned_number = cleaned_number_digits
    if not final_cleaned_number or (has_plus and len(final_cleaned_number) <= 1) or len(cleaned_number_digits) < 4:
        return f"Error: Invalid phone number format provided or too short ('{recipient_number}' -> '{final_cleaned_number}')."
    # --- End Number Cleaning ---

    tel_uri = f"tel:{final_cleaned_number}"
    adb_command_args = ["shell", "am", "start", "-a", "android.intent.action.CALL", "-d", tel_uri]

    # --- SIM Slot handling (Keep As Is) ---
    sim_slot_message = ""
    if sim_slot is not None:
        try:
            slot_index = int(sim_slot)
            if slot_index in [0, 1]:
                adb_command_args.extend(["--ei", "com.android.phone.extra.slot", slot_index])
                sim_slot_message = f" (attempting to use SIM slot {slot_index + 1})"
                logging.info(f"Attempting to specify SIM slot index: {slot_index}")
            else:
                logging.warning(f"Invalid SIM slot index provided: {sim_slot}. Ignoring.")
                sim_slot_message = " (invalid SIM slot specified, using default)"
        except ValueError:
            logging.warning(f"Invalid SIM slot value provided: {sim_slot}. Must be an integer (0 or 1). Ignoring.")
            sim_slot_message = " (invalid SIM slot specified, using default)"
    # --- End SIM Slot handling ---

    # --- Pass target_device_id to run_adb_command ---
    success, output = run_adb_command(adb_command_args, device_id=target_device_id)
    if success:
        # --- MASK THE NUMBER ---
        masked_number = mask_phone_number(final_cleaned_number)
        logging.info(f"ADB command to initiate call to {masked_number}{sim_slot_message} sent.") # Log masked number

        # --- SHORTENED BASE MESSAGE ---
        base_message = f"Okay, calling {masked_number}{sim_slot_message}."

        confirmation_needed_message = " Check phone screen." # Shortened
        output_lower = output.lower() if output else "" # Check output even if RC=0

        # Check for errors reported by 'am start' even on success RC
        if "error" in output_lower or "unable to resolve intent" in output_lower or "activity not started" in output_lower or "permission denial" in output_lower:
             if "permission denial" in output_lower:
                  logging.error(f"Command failed due to permissions. Grant CALL_PHONE or use DIAL. Output: {output}")
                  # Return specific error, still masked number
                  return f"Sorry, failed to call {masked_number} due to missing permissions. Check logs."
             elif "com.android.phone.extra.slot" in output_lower:
                  logging.warning(f"Command sent, but device reported issue resolving SIM slot extra: {output}")
                  # Return modified message
                  return base_message + confirmation_needed_message + " (Note: SIM selection might not have worked)."
             else:
                  logging.error(f"Command sent (RC=0), but device reported an error starting the call intent: {output}")
                  # Return generic device error, still masked number
                  return f"Sorry, device reported an error trying to call {masked_number}. Error: {output}"
        else:
             # --- SUCCESS RETURN ---
             return base_message + confirmation_needed_message
    else:
        # --- FAILURE RETURN (Keep error details from run_adb_command) ---
        # Mask number in log if possible, but return original error message from run_adb_command
        masked_number = mask_phone_number(final_cleaned_number)
        logging.error(f"Failed to send call command for {masked_number}. ADB Error: {output}")
        return f"Sorry, failed to send call command. {output}" # Output already contains error details
    # --- End Result Handling ---

    # --- Result handling (Keep As Is, but log target device) ---
    # device_msg = f" on device {target_device_id}" if target_device_id else ""
    # if success:
    #     logging.info(f"ADB command to initiate call to {final_cleaned_number}{sim_slot_message}{device_msg} sent.")
    #     base_message = f"Okay, I've sent the command{device_msg} to start a call to {final_cleaned_number}{sim_slot_message}."
    #     confirmation_needed_message = " Please check your phone screen, you might need to confirm the call"
    #     output_lower = output.lower()
    #     if "error" in output_lower or "unable to resolve intent" in output_lower or "activity not started" in output_lower:
    #          if "com.android.phone.extra.slot" in output_lower:
    #               logging.warning(f"Command sent{device_msg}, but device reported issue resolving SIM slot extra: {output}")
    #               return base_message + confirmation_needed_message + " (Note: SIM selection might not have worked)."
    #          else:
    #               logging.error(f"Command sent{device_msg} (RC=0), but device reported an error starting the call intent: {output}")
    #               return f"Sorry, the command was sent{device_msg} but the device reported an error trying to start the call: {output}"
    #     else:
    #          return base_message + confirmation_needed_message
    # else:
    #     return f"Sorry, I failed to send the call command via ADB{device_msg}. {output}"
    # --- End Result Handling ---
def get_sim_slot_choice():
    """
    Gets the user's SIM slot choice and validates the input.
    Returns:
        tuple: (selected_sim_slot, message)
        - selected_sim_slot: int or None (0 for SIM1, 1 for SIM2, None for default)
        - message: str (descriptive message about the selection)
    """
    selected_sim_slot = None
    sim_choice = input("Enter SIM slot to use (1 or 2, leave blank for default): ").strip()
    
    if not sim_choice:
        return None, "Using default SIM slot"
    
    try:
        choice = int(sim_choice)
        if choice == 1:
            selected_sim_slot = 0
            message = "Using SIM 1"
        elif choice == 2:
            selected_sim_slot = 1
            message = "Using SIM 2"
        else:
            message = "Invalid SIM choice (must be 1 or 2), using default SIM slot"
            selected_sim_slot = None
    except ValueError:
        message = "Invalid input (must be 1 or 2), using default SIM slot"
        selected_sim_slot = None

    logging.info(f"SIM slot selection: {message}")
    return selected_sim_slot, message

def end_call_adb(device_id: str = None):
    """
    Ends/Cancels the current phone call using ADB commands.
    Args:
        device_id (str, optional): Target specific device if multiple connected
    Returns:
        tuple: (success: bool, message: str)
    """
    logging.info("Attempting to end current call...")
    
    # Try multiple methods to ensure compatibility
    end_call_commands = [
        ["shell", "input", "keyevent", "KEYCODE_ENDCALL"],  # Most compatible method
        ["shell", "service", "call", "telecom", "8"],       # Modern Android method
        ["shell", "input", "keyevent", "6"],                # Alternative keycode
    ]
    
    for cmd in end_call_commands:
        success, output = run_adb_command(cmd, device_id=device_id)
        if success and "error" not in output.lower():
            logging.info("Call end command sent successfully")
            return True, "Call end command sent successfully"
            
    return False, "Failed to end call. You may need to end it manually on the device"

def toggle_speaker_adb(device_id: str = None, speaker_on: bool = None):
    """
    Toggles or sets the speaker phone state during a call using multiple methods,
    including dynamic UI tapping for better reliability.

    Args:
        device_id (str, optional): Target specific device if multiple connected.
        speaker_on (bool, optional): If provided, explicitly set speaker state
                                     (True=on, False=off). If None, toggles.

    Returns:
        tuple: (success: bool, message: str)
    """
    target_state = "speakerphone"
    if speaker_on is True:
        target_state = "ON"
    elif speaker_on is False:
        target_state = "OFF"

    logging.info(f"Attempting to set speaker phone {target_state} on device {device_id or 'default'}...")
    success_achieved = False

    # --- Method 1: Service Call (Try first for explicit ON/OFF) ---
    # Android 13 IAudioService setSpeakerphoneOn is often #11
    # This might be more reliable for SETTING state than toggling via UI
    if speaker_on is not None:
        tx_id = "79"
        arg = "1" if speaker_on else "0"
        cmd = [
                ["shell", "input", "keyevent", "KEYCODE_HEADSETHOOK", "79"],  # Most compatible method
                ["shell", "service", "call", "audio", tx_id, "i32", arg],
                ["shell", "input", "keyevent", "KEYCODE_HEADSETHOOK"],  # Most compatible method
                ["shell", "service", "call", "audio", "12"],       # Modern Android method
                ["shell", "input", "keyevent", "KEYCODE_HEADSETHOOK", "79"],
                ]
        logging.info(f"Trying method: Service Call audio {tx_id} setSpeakerphoneOn({speaker_on})")
        ok, out = run_adb_command(cmd, device_id=device_id)
        # Check for success (often returns "Result: Parcel(NULL)")
        if ok and ("parcel" in out.lower() or not out.strip()):
            logging.info("Service call command sent successfully.")
            # Optional: Verify state via dumpsys audio if needed, but can be slow
            # v_ok, v_out = run_adb_command(["shell", "dumpsys", "audio"], device_id)
            # if v_ok and "ROUTE_SPEAKER" in v_out.upper(): ...
            success_achieved = True
            # Return early as this is often the most direct method if it works
            return True, f"Speakerphone {'ON' if speaker_on else 'OFF'} attempt via service call sent. Check device."
        else:
            logging.warning(f"Service call audio {tx_id} failed or output unexpected. Output: {out}")
        time.sleep(0.5)


    # --- Method 2: Dynamic UI Automator Tap (Good for TOGGLE or fallback) ---
    # Only proceed if service call didn't succeed or if toggling (speaker_on is None)
    if not success_achieved or speaker_on is None:
        logging.info("Trying method: UI Automator Tap")
        dump_path_device = "/sdcard/window_dump.xml"
        dump_path_local = "window_dump.xml" # Local temporary file name
        speaker_node = None
        center_x, center_y = 870, 2100

        # Clean up previous local dump if it exists
        if os.path.exists(dump_path_local):
            try:
                os.remove(dump_path_local)
            except OSError as e:
                logging.warning(f"Could not remove previous local dump file {dump_path_local}: {e}")

        # 1. Dump UI on device
        dump_success, dump_output = run_adb_command(["shell", "uiautomator", "dump", dump_path_device], device_id=device_id)
        if not dump_success:
            logging.warning(f"Failed to dump UI using uiautomator: {dump_output}")
            # Fall through to next method

        else: # Dump succeeded, now pull and parse
            time.sleep(1) # Give dump time to finish writing

            # 2. Pull dump file
            pull_success, pull_output = run_adb_command(["pull", dump_path_device, dump_path_local], device_id=device_id)
            if not pull_success:
                logging.warning(f"Failed to pull UI dump file {dump_path_device}: {pull_output}")
                # Fall through to next method
            else: # Pull succeeded, now parse
                # 3. Parse XML to find speaker button
                try:
                    tree = ET.parse(dump_path_local)
                    root = tree.getroot()

                    # --- !!! IMPORTANT: ADAPT THESE IDENTIFIERS FOR YOUR DEVICE !!! ---
                    # Inspect your window_dump.xml during a call to find the correct ID or description
                    possible_ids = [
                        "com.android.incallui:id/speakerButton",     # AOSP/Pixel?
                        "com.google.android.dialer:id/speaker_button", # Google Dialer app
                        "com.samsung.android.incallui:id/speaker_button", # Example Samsung
                        # Add other potential IDs based on your device's Dialer app
                    ]
                    # Content description can be language-dependent
                    possible_descs_keywords = ["speaker", "speakerphone", "lautsprecher"] # English, German example
                    # --- End Adaptable Identifiers ---

                    for node in root.iter('node'):
                        res_id = node.get('resource-id', '')
                        desc = node.get('content-desc', '').lower()
                        bounds = node.get('bounds')
                        # Ensure the node is clickable and visible (optional but good)
                        is_clickable = node.get('clickable') == 'true'
                        # is_visible = node.get('visible-to-user') == 'true' # Might not always be present

                        if bounds and is_clickable: # Only consider clickable nodes with bounds
                            # Check resource-id first
                            if res_id in possible_ids:
                                speaker_node = node
                                logging.info(f"Found speaker button node by resource-id: {res_id}")
                                break
                            # Check content-desc if ID didn't match
                            if not speaker_node:
                                 for keyword in possible_descs_keywords:
                                     if keyword in desc:
                                         speaker_node = node
                                         logging.info(f"Found speaker button node by content-desc: {node.get('content-desc')}")
                                         break # Found via desc keyword
                            if speaker_node: break # Exit outer loop if found

                    if speaker_node:
                        # 4. Extract bounds and calculate center
                        bounds_str = speaker_node.get('bounds')
                        match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
                        if match:
                            x1, y1, x2, y2 = map(int, match.groups())
                            if x1 < x2 and y1 < y2: # Basic sanity check
                                 center_x = (x1 + x2) // 2
                                 center_y = (y1 + y2) // 2
                                 logging.info(f"Calculated speaker button center: ({center_x}, {center_y}) from bounds {bounds_str}")
                            else:
                                 logging.warning(f"Invalid bounds found for speaker button: {bounds_str}")
                        else:
                            logging.warning(f"Could not parse bounds string: {bounds_str}")
                    else:
                        logging.warning("Speaker button node not found in UI dump. Check possible_ids/possible_descs_keywords.")

                except ET.ParseError as e:
                    logging.error(f"Failed to parse UI dump XML file {dump_path_local}: {e}")
                except Exception as e:
                    logging.error(f"An error occurred during UI dump parsing: {e}", exc_info=True)
                finally:
                     # Clean up local dump file
                     if os.path.exists(dump_path_local):
                         try:
                             os.remove(dump_path_local)
                         except OSError as e:
                             logging.warning(f"Could not remove local dump file {dump_path_local}: {e}")

            # 5. Perform Tap if coordinates were found
            if center_x is not None and center_y is not None:
                tap_success, tap_output = run_adb_command(["shell", "input", "tap", str(center_x), str(center_y)], device_id=device_id)
                if tap_success:
                    logging.info("Speaker toggled via UI tap.")
                    success_achieved = True
                    # Give a moment for UI to react
                    time.sleep(1)
                    # Return success after tap
                    return True, "Speaker toggled via UI tap"
                else:
                    logging.warning(f"UI tap command failed: {tap_output}")
                    # Fall through to headset hook

            # Clean up dump on device (best effort, do regardless of parsing success)
            run_adb_command(["shell", "rm", dump_path_device], device_id)


    # --- Method 3: Headset-hook fallback ---
    if not success_achieved:
        logging.info("Trying method: Input Keyevent HEADSETHOOK (fallback toggle)")
        ok, _ = run_adb_command(["shell", "input", "keyevent", "KEYCODE_HEADSETHOOK"], device_id)
        if ok:
            success_achieved = True
            return True, "Speaker toggled via headset-hook keyevent (fallback)"

    # --- Final Failure ---
    if not success_achieved:
        return False, "Failed to toggle speaker after trying multiple methods."
    # Should not be reached if logic is correct, but as a safeguard:
    return success_achieved, "Speaker toggle attempt finished."

def take_screenshot_adb(local_filename=None, device_id=None):
    """
    Takes a screenshot of the connected device and saves it locally,
    preferably in a folder named after the sanitized device_id.

    Args:
        local_filename (str, optional): The desired base local filename (e.g., "my_screenshot.png").
                                         If None, a timestamped filename will be generated.
        device_id (str, optional): Target specific device. Highly recommended for saving into a device-specific folder.

    Returns:
        tuple: (success: bool, message: str)
    """
    
    device_screenshot_path = "sdcard/DCIM/Screenshots/screenshot_temp.png"
    save_directory = "./phonescreenshot/" # Default to current directory

    if device_id:
        # Sanitize the device_id to create a valid folder name
        # sanitized_device_id_folder = sanitize_filename(device_id)
        # save_directory = sanitized_device_id_folder
        logging.info(f"Targeting save directory based on device ID: {save_directory}")
    else:
        logging.warning("No device_id provided. Screenshot will be saved in the current directory.")

    # Create the target directory if it doesn't exist
    try:
        # exist_ok=True prevents error if directory already exists
        os.makedirs(save_directory, exist_ok=True)
        logging.debug(f"Ensured directory exists: {save_directory}")
    except OSError as e:
        logging.error(f"Failed to create directory '{save_directory}': {e}")
        return False, f"Failed to create directory '{save_directory}': {e}"

    # Generate base filename if not provided
    if local_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"screenshot_{timestamp}.png"
    elif not local_filename.lower().endswith(".png"):
        base_filename = local_filename + ".png"
    else:
        base_filename = local_filename

    # Construct the full local path including the directory
    full_local_path = os.path.join(save_directory, base_filename)

    logging.info(f"Attempting to take screenshot on device {device_id or 'default'}...")

    # 1. Take screenshot on device
    cmd_screencap = ["shell", "screencap", "-p", device_screenshot_path]
    cap_success, cap_output = run_adb_command(cmd_screencap, device_id=device_id)
    if not cap_success:
        logging.error(f"Failed to capture screenshot on device: {cap_output}")
        # Clean up potentially failed/partial file on device before returning
        run_adb_command(["shell", "rm", device_screenshot_path], device_id)
        return False, f"Failed to capture screenshot on device: {cap_output}"
    time.sleep(1) # Allow time for file write

    # 2. Pull the screenshot file to the full local path
    logging.info(f"Pulling screenshot from {device_screenshot_path} to {full_local_path}...")
    cmd_pull = ["pull", device_screenshot_path, full_local_path] # Use full path
    pull_success, pull_output = run_adb_command(cmd_pull, device_id=device_id)

    # 3. Clean up screenshot file on device (always attempt)
    logging.info(f"Removing temporary screenshot from device: {device_screenshot_path}...")
    rm_success, rm_output = run_adb_command(["shell", "rm", device_screenshot_path], device_id=device_id)
    if not rm_success:
        logging.warning(f"Failed to remove temporary screenshot {device_screenshot_path} from device: {rm_output}")

    # Check pull result
    if pull_success:
        abs_path = os.path.abspath(full_local_path)
        logging.info(f"Screenshot saved successfully to: {abs_path}")
        return True, f"Screenshot saved to: {abs_path}"
    else:
        logging.error(f"Failed to pull screenshot from device: {pull_output}")
        # If pull failed, the local file might be incomplete or non-existent
        return False, f"Failed to pull screenshot: {pull_output}"

def sanitize_filename(filename):
    """
    Sanitizes a filename by removing or replacing invalid characters.
    This is useful for creating valid directory names based on device IDs.
    """
    # Define a regex pattern to match invalid characters
    invalid_chars_pattern = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars_pattern, '_', filename)
    return sanitized

def get_battery_percentage_adb(device_id=None):
    """
    Gets the current battery level percentage from the connected device.

    Args:
        device_id (str, optional): Target specific device if multiple connected.

    Returns:
        tuple: (success: bool, result: int or str)
               If success, result is the battery percentage (int).
               If failure, result is an error message (str).
    """
    logging.info(f"Attempting to get battery level for device {device_id or 'default'}...")

    # Command to get battery information
    cmd_battery = ["shell", "dumpsys", "battery"]
    success, output = run_adb_command(cmd_battery, device_id=device_id)

    if not success:
        logging.error(f"Failed to get battery info: {output}")
        return False, f"Failed to get battery info: {output}"

    # Parse the output to find the level
    try:
        # Use regex to find the line 'level: XX'
        match = re.search(r'^\s*level:\s*(\d+)', output, re.MULTILINE)
        if match:
            battery_level = int(match.group(1))
            logging.info(f"Found battery level: {battery_level}%")
            return True, battery_level
        else:
            logging.warning(f"Could not parse battery level from dumpsys output:\n{output}")
            return False, "Could not parse battery level from output."
    except ValueError:
        logging.error("Error converting battery level to integer.")
        return False, "Error converting battery level to integer."
    except Exception as e:
        logging.error(f"An unexpected error occurred parsing battery info: {e}", exc_info=True)
        return False, f"An unexpected error occurred parsing battery info: {e}"

def handle_call_audio_controls():
    """
    Provides a menu for controlling call audio settings
    """
    while True:
        print("\nCall Audio Controls:")
        print("1: Turn Speaker ON")
        print("2: Turn Speaker OFF")
        print("3: Toggle Speaker")
        print("4: Return to main menu")
        
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            success, message = toggle_speaker_adb(speaker_on=True)
            print(f"\nResult: {message}")
        elif choice == "2":
            success, message = toggle_speaker_adb(speaker_on=False)
            print(f"\nResult: {message}")
        elif choice == "3":
            success, message = toggle_speaker_adb()
            print(f"\nResult: {message}")
        elif choice == "4":
            print("Returning to main menu...")
            break
        else:
            print("Invalid choice. Please try again.")


# # --- Main Execution Block (MODIFIED for Wi-Fi Connection Logic) ---
# if __name__ == "__main__":
#     print(f"--- ADB Call Assistant (Using '{CONTACT_FILE_PATH}') ---")

#     # 1. Initial ADB Check
#     print("Performing initial ADB connection check...")
#     check_ok, devices, error_msg = check_adb_connection()

#     if not check_ok:
#         print(error_msg)
#         sys.exit(1)

#     authorized_device_id = None
#     connection_type = None
#     usb_device_id_for_wifi = None # Track a potential USB candidate

#     # Find the first authorized device (prefer Wi-Fi if available)
#     for dev_id, status, conn_type in devices:
#         if status == 'device':
#             if conn_type == 'wifi':
#                 authorized_device_id = dev_id
#                 connection_type = 'wifi'
#                 print(f"Found authorized device connected via Wi-Fi: {authorized_device_id}")
#                 break # Prefer Wi-Fi, stop searching
#             elif conn_type == 'usb' and not authorized_device_id: # Found USB, no Wi-Fi yet
#                 authorized_device_id = dev_id
#                 connection_type = 'usb'
#                 usb_device_id_for_wifi = dev_id # This is our candidate for switching
#                 print(f"Found authorized device connected via USB: {authorized_device_id}")
#                 # Don't break, keep looking for Wi-Fi
#             elif not authorized_device_id: # Found unknown type, no Wi-Fi/USB yet
#                     authorized_device_id = dev_id
#                     connection_type = 'unknown'
#                     print(f"Found authorized device with unknown connection type: {authorized_device_id}")

#         elif status == 'unauthorized':
#             print(f"Warning: Found unauthorized device: {dev_id}. Please allow USB debugging on the device.")
#         elif status == 'offline':
#             print(f"Warning: Found offline device: {dev_id}. Please check connection.")

#     # 2. Attempt Wi-Fi Connection if only USB is found
#     if connection_type == 'usb' and usb_device_id_for_wifi:
#         print("\nUSB connection found. Attempting to switch to Wi-Fi ADB...")
#         wifi_success, wifi_device_addr = connect_adb_wifi(usb_device_id_for_wifi)
#         if wifi_success:
#             authorized_device_id = wifi_device_addr # Update to use the Wi-Fi ID
#             connection_type = 'wifi'
#             print(f"Switched to Wi-Fi connection: {authorized_device_id}")
#         else:
#             print("Failed to switch to Wi-Fi ADB. Continuing with USB connection (if possible).")
#             # Keep authorized_device_id as the USB one

#     # 3. Final Check and Exit if No Authorized Device
#     if not authorized_device_id:
#         print("\nError: No authorized ADB device found.")
#         print("Please ensure your device is connected (initially via USB), USB debugging is enabled,")
#         print("and you have authorized the connection on the device screen.")
#         sys.exit(1)

#     print(f"\nProceeding with device: {authorized_device_id} (Type: {connection_type})")

#     # --- Rest of the script (using authorized_device_id) ---

#     # 4. Get Contact Name or Number
#     target_number = None
#     user_input = input("\nEnter contact name or phone number to call: ").strip()

#     if not user_input:
#         print("No input provided.")
#         sys.exit(1)

#     # --- Phone Number Check (Keep As Is) ---
#     digit_count = len(re.findall(r'\d', user_input))
#     allowed_chars_pattern = r'^[+\-()\s\d]*$'
#     has_only_allowed_chars = re.fullmatch(allowed_chars_pattern, user_input) is not None
#     if digit_count >= 5 and has_only_allowed_chars:
#             print("Input looks like a phone number.")
#             target_number = user_input
#             number_source_message = f"Using provided number: {target_number}"
#     # --- End Phone Number Check ---
#     else:
#         # Treat as name
#         if not has_only_allowed_chars: print(f"Input '{user_input}' contains disallowed characters. Treating as a name.")
#         elif digit_count < 5: print(f"Input '{user_input}' has fewer than 5 digits. Treating as a name.")
#         else: print(f"Input '{user_input}' does not meet phone number criteria. Treating as a name.")

#         print(f"Searching '{CONTACT_FILE_NAME}' for name...")
#         found_number, search_message = get_contact_number_from_file(user_input)
#         print(search_message)
#         if found_number:
#             target_number = found_number
#             number_source_message = f"Using number from '{CONTACT_FILE_NAME}': {target_number}"
#         else:
#             sys.exit(1)

#     # get sim slot choice using get_sim_slot_choice
#     selected_sim_slot, sim_slot_message = get_sim_slot_choice()
#     print(sim_slot_message)
#     call_result = make_phone_call_adb(target_number, sim_slot=selected_sim_slot, target_device_id=authorized_device_id)
#     print(f"\nCall Result: {call_result}")
#     # --- End SIM Slot Choice --

#     while True:
#         print("\nCall Control Options:")
#         print("1: End current call")
#         print("2: Audio Controls")
#         print("3: Take Screenshot")
#         print("4: battery level")
#         print("5: Exit")
#         choice = input("Enter your choice (1-5): ").strip()
        
#         if choice == "1":
#             success, message = end_call_adb(authorized_device_id)
#             print(f"\nResult: {message}")
#             if success:
#                 break
#         elif choice == "2":
#             handle_call_audio_controls()
#         elif choice == "3":
#             success, message = take_screenshot_adb(device_id=authorized_device_id)
#             print(f"\nResult: {message}")
#         elif choice == "4":
#             success, message = get_battery_percentage_adb(authorized_device_id)
#             print(f"\nResult: {message}")
#         elif choice == "5":
#             print("Exiting...")
#             break
#         else:
#             print("Invalid choice. Please try again.")

#     # 5. Get SIM Slot Choice
#     selected_sim_slot = None
#     if target_number:
#         print(f"\n{number_source_message}")
#         sim_choice = input("Enter SIM slot to use (1 or 2, leave blank for default): ").strip()
#         if sim_choice == '1': selected_sim_slot = 0; print("Attempting to use SIM 1.")
#         elif sim_choice == '2': selected_sim_slot = 1; print("Attempting to use SIM 2.")
#         elif sim_choice: print("Invalid SIM choice, using default.")
#         else: print("Using default SIM slot.")

#         # 6. Make the Call (Pass the target device ID)
#         call_result = make_phone_call_adb(target_number, sim_slot=selected_sim_slot, target_device_id=authorized_device_id)
#         print(f"\nCall Result: {call_result}")

#     else:
#         print("\nCould not determine a phone number to call.")

























    # # Automation/adb_call.py

    # import subprocess
    # import logging
    # import platform
    # import shlex
    # import sys
# import re
# import os.path

# # --- Google API Imports ---
# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
# # --- End Google API Imports ---

# # --- ADDED: dotenv import ---
# from dotenv import dotenv_values
# # --- End dotenv import ---

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# # --- Determine Project Root and Load .env ---
# AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT = os.path.dirname(AUTOMATION_DIR) # Go one level up to project root
# ENV_PATH = os.path.join(PROJECT_ROOT, '.env')
# config = dotenv_values(ENV_PATH)
# # --- End .env Loading ---

# # --- Google API Constants / Credentials from .env ---
# SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']
# TOKEN_FILE = os.path.join(AUTOMATION_DIR, 'token.json') # Path relative to script

# # Get credentials from loaded .env config
# GOOGLE_CLIENT_ID = config.get("GOOGLE_CLIENT_ID")
# GOOGLE_CLIENT_SECRET = config.get("GOOGLE_CLIENT_SECRET")

# # REMOVED: CLIENT_SECRET_FILE constant is no longer needed directly
# # CLIENT_SECRET_FILE = os.path.join(AUTOMATION_DIR, 'client_secret.json')
# # --- End Google API Constants ---


# # --- run_adb_command function (Keep As Is) ---
# def run_adb_command(command_args):
#     # ... (function code remains unchanged) ...
#     """Helper function to run ADB commands."""
#     if platform.system() == 'Windows':
#         adb_executable = "adb" # Or provide full path if needed
#     else: # macOS or Linux
#         adb_executable = "adb"

#     full_command = [adb_executable] + command_args
#     # logging.info(f"Running ADB command: {' '.join(shlex.quote(str(arg)) for arg in full_command)}")

#     try:
#         string_command = [str(arg) for arg in full_command]
#         result = subprocess.run(string_command, capture_output=True, text=True, check=False, timeout=25)

#         stdout_lower = result.stdout.lower() if result.stdout else ""
#         stderr_lower = result.stderr.lower() if result.stderr else ""
#         combined_output_lower = stdout_lower + stderr_lower

#         if "error: device unauthorized" in combined_output_lower or "unauthorized" in combined_output_lower:
#              error_msg = "Device unauthorized. Please check the prompt on your Android phone and allow USB debugging."
#             #  logging.error(f"ADB command failed: {error_msg}")
#              return False, error_msg
#         elif "error: device offline" in combined_output_lower or "offline" in combined_output_lower:
#              error_msg = "Device offline. Please ensure it's connected properly and awake."
#             #  logging.error(f"ADB command failed: {error_msg}")
#              return False, error_msg
#         elif ("error: device" in combined_output_lower and "not found" in combined_output_lower) or "no devices/emulators found" in combined_output_lower:
#              error_msg = "Device not found. Ensure it's connected, USB debugging is enabled, and authorized."
#             #  logging.error(f"ADB command failed: {error_msg}")
#              return False, error_msg

#         if result.returncode == 0:
#             if "content query" in full_command:
#                 #  logging.info(f"ADB content query successful (RC=0). Output length: {len(result.stdout)}")
#                  if result.stdout: logging.debug("ADB Output (first 5 lines):\n" + "\n".join(result.stdout.splitlines()[:5]))
#                  return True, result.stdout.strip()
#             elif "am start" in full_command:
#                  if "starting: intent" in stdout_lower:
#                     #   logging.info(f"ADB 'am start' likely successful. Output:\n{result.stdout.strip()}")
#                       return True, result.stdout.strip()
#                  else:
#                     #   logging.warning(f"ADB 'am start' executed (RC=0), but output needs inspection:\n{result.stdout.strip()}")
#                       return True, result.stdout.strip()
#             else:
#                 #  logging.info(f"ADB command successful (RC=0). Output:\n{result.stdout.strip()}")
#                  return True, result.stdout.strip()
#         else:
#             error_output = result.stderr.strip() if result.stderr else result.stdout.strip()
#             if not error_output: error_output = f"ADB command failed with return code {result.returncode}"
#             # logging.error(f"ADB command failed. Return code: {result.returncode}. Error:\n{error_output}")
#             identified_error = next((msg for err_key, msg in {
#                 "unauthorized": "Device unauthorized.", "offline": "Device offline.", "not found": "Device not found."
#             }.items() if err_key in error_output.lower()), None)
#             return False, f"Error: {identified_error or error_output}"

#     except FileNotFoundError:
#         # logging.error("ADB command failed: 'adb' executable not found.")
#         return False, "Error: 'adb' command not found. Install Android Platform Tools and ensure it's in PATH."
#     except subprocess.TimeoutExpired:
#         # logging.error("ADB command timed out.")
#         return False, "Error: ADB command timed out."
#     except Exception as e:
#         # logging.error(f"An unexpected error occurred running ADB command: {e}", exc_info=True)
#         return False, f"An unexpected error occurred: {e}"


# # --- Google Authentication Function (MODIFIED) ---
# def authenticate_google():
#     """Handles Google OAuth 2.0 authentication flow using credentials from .env."""
#     creds = None
#     if os.path.exists(TOKEN_FILE):
#         try:
#             creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
#             logging.debug(f"Loaded credentials from {TOKEN_FILE}")
#         except Exception as e:
#             logging.warning(f"Could not load credentials from {TOKEN_FILE}: {e}. Re-authentication might be needed.")
#             creds = None

#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             try:
#                 logging.info("Refreshing expired Google credentials...")
#                 creds.refresh(Request())
#                 logging.info("Credentials refreshed successfully.")
#                 try:
#                     with open(TOKEN_FILE, 'w') as token: token.write(creds.to_json())
#                     logging.info(f"Refreshed credentials saved to {TOKEN_FILE}")
#                 except Exception as e_save: logging.error(f"Failed to save refreshed credentials to {TOKEN_FILE}: {e_save}")
#             except Exception as e_refresh:
#                 logging.error(f"Failed to refresh credentials: {e_refresh}. Need to re-authenticate.")
#                 try:
#                     if os.path.exists(TOKEN_FILE): os.remove(TOKEN_FILE)
#                     logging.info(f"Removed potentially invalid token file: {TOKEN_FILE}")
#                 except OSError as e_remove: logging.error(f"Error removing token file {TOKEN_FILE}: {e_remove}")
#                 creds = None
#         else:
#             logging.info("No valid Google credentials found or refresh failed. Starting authentication flow...")
#             # --- MODIFICATION: Use credentials from .env ---
#             if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
#                 logging.error("GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not found in .env file. Cannot authenticate.")
#                 return None

#             # Construct client_config dictionary
#             client_config = {
#                 "installed": {
#                     "client_id": GOOGLE_CLIENT_ID,
#                     "client_secret": GOOGLE_CLIENT_SECRET,
#                     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#                     "token_uri": "https://oauth2.googleapis.com/token",
#                     # Add redirect_uris if needed, often defaults work for localhost
#                     # "redirect_uris": ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"]
#                 }
#             }
#             # --- End Modification ---

#             try:
#                 # --- MODIFICATION: Use from_client_config instead of from_client_secrets_file ---
#                 flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
#                 # --- End Modification ---
#                 creds = flow.run_local_server(port=0, authorization_prompt_message="Please authorize access to Google Contacts:\n{url}", success_message="Authentication successful! You can close this browser tab.")
#                 logging.info("Authentication successful.")
#                 try:
#                     with open(TOKEN_FILE, 'w') as token: token.write(creds.to_json())
#                     logging.info(f"Credentials saved to {TOKEN_FILE}")
#                 except Exception as e_save: logging.error(f"Failed to save new credentials to {TOKEN_FILE}: {e_save}")
#             except Exception as e_flow:
#                 logging.error(f"Authentication flow failed: {e_flow}", exc_info=True)
#                 return None

#     return creds


# # --- Google Contact Search Function (get_contact_number_google - Keep As Is) ---
# def get_contact_number_google(name_query: str):
#     # ... (function code remains unchanged) ...
#     """Searches Google Contacts for a name and returns the selected phone number."""
#     creds = authenticate_google()
#     if not creds:
#         return None, "Google Authentication failed. Cannot search contacts."

#     try:
#         service = build('people', 'v1', credentials=creds, static_discovery=False)
#         logging.info(f"Searching Google Contacts for name containing: '{name_query}'")

#         results = service.people().connections().list(
#             resourceName='people/me',
#             pageSize=50, # Adjust page size as needed
#             personFields='names,phoneNumbers'
#         ).execute()

#         connections = results.get('connections', [])
#         found_contacts = []

#         if not connections:
#             logging.info("No Google Contacts found in the account.")
#             if 'connections' in results:
#                  return None, "No Google Contacts found in your account."
#             else:
#                  logging.warning("Google People API response did not contain a 'connections' field.")
#                  return None, "Could not retrieve contacts from Google. API response might be unusual."


#         for person in connections:
#             names = person.get('names', [])
#             if names:
#                 display_name = names[0].get('displayName', '')
#                 if display_name and name_query.lower() in display_name.lower():
#                     found_contacts.append(person)

#         if not found_contacts:
#             logging.info(f"No contact found matching '{name_query}'.")
#             return None, f"Sorry, I couldn't find a contact matching '{name_query}' in your Google Contacts."

#         selected_person = None
#         if len(found_contacts) == 1:
#             selected_person = found_contacts[0]
#             logging.info(f"Found unique contact: {selected_person.get('names', [{}])[0].get('displayName')}")
#         else:
#             print(f"\nFound multiple contacts matching '{name_query}':")
#             for i, person in enumerate(found_contacts):
#                 print(f"  {i + 1}: {person.get('names', [{}])[0].get('displayName')}")
#             while True:
#                 try:
#                     choice = input(f"Which contact do you mean? (Enter number 1-{len(found_contacts)}): ")
#                     index = int(choice) - 1
#                     if 0 <= index < len(found_contacts):
#                         selected_person = found_contacts[index]
#                         break
#                     else:
#                         print("Invalid choice. Please enter a number from the list.")
#                 except ValueError:
#                     print("Invalid input. Please enter a number.")
#             logging.info(f"User selected contact: {selected_person.get('names', [{}])[0].get('displayName')}")

#         phone_numbers = selected_person.get('phoneNumbers', [])
#         if not phone_numbers:
#             name = selected_person.get('names', [{}])[0].get('displayName')
#             logging.warning(f"Contact '{name}' found, but has no phone numbers listed.")
#             return None, f"Contact '{name}' doesn't have any phone numbers saved in Google Contacts."

#         valid_numbers = []
#         number_details = []
#         for number_entry in phone_numbers:
#             num_value = number_entry.get('value')
#             if num_value:
#                  num_type = number_entry.get('formattedType', number_entry.get('type', 'Other'))
#                  valid_numbers.append(num_value)
#                  number_details.append((num_type, num_value))

#         if not valid_numbers:
#              name = selected_person.get('names', [{}])[0].get('displayName')
#              logging.warning(f"Contact '{name}' has phone number entries, but no actual numbers could be extracted.")
#              return None, f"Contact '{name}' seems to have phone number entries, but no actual numbers are saved or could be read."

#         if len(valid_numbers) == 1:
#             number_value = valid_numbers[0]
#             logging.info(f"Using number: {number_value}")
#             return number_value, f"Found number {number_value} for {selected_person.get('names', [{}])[0].get('displayName')}."
#         else:
#             print(f"\nContact {selected_person.get('names', [{}])[0].get('displayName')} has multiple numbers:")
#             for i, (num_type, num_value) in enumerate(number_details):
#                 print(f"  {i + 1}: {num_type} - {num_value}")

#             while True:
#                 try:
#                     choice = input(f"Which number do you want to call? (Enter number 1-{len(valid_numbers)}): ")
#                     index = int(choice) - 1
#                     if 0 <= index < len(valid_numbers):
#                         selected_number = valid_numbers[index]
#                         logging.info(f"User selected number: {selected_number}")
#                         return selected_number, f"Using number {selected_number}."
#                     else:
#                         print("Invalid choice. Please enter a number from the list.")
#                 except ValueError:
#                     print("Invalid input. Please enter a number.")

#     except HttpError as err:
#         logging.error(f"An error occurred calling the Google People API: {err}", exc_info=True)
#         if err.resp.status == 403:
#              if "service not enabled" in str(err).lower() or "api not enabled" in str(err).lower(): error_msg = "Error: The Google People API is not enabled for your project in Google Cloud Console. Please enable it."
#              else: error_msg = "Error: Permission denied accessing Google Contacts. Check API permissions or re-authenticate."
#              logging.error(error_msg)
#              return None, error_msg
#         elif err.resp.status == 401:
#              logging.error("Error: Google authentication failed (401 Unauthorized). Token might be invalid. Try deleting token.json and re-running.")
#              return None, "Error: Google authentication failed. Please try running the script again to re-authenticate."
#         return None, f"An error occurred while searching Google Contacts: {err}"
#     except Exception as e:
#         logging.error(f"An unexpected error occurred during Google contact search: {e}", exc_info=True)
#         return None, f"An unexpected error occurred during Google contact search: {e}"


# # --- make_phone_call_adb function (Keep As Is) ---
# def make_phone_call_adb(recipient_number: str, sim_slot: int = None):
#     # ... (function code remains unchanged) ...
#     """
#     Attempts to initiate a phone call on a connected Android device using ADB,
#     optionally trying to specify a SIM slot.
#     """
#     if not recipient_number:
#         return "Error: Please provide a phone number to call."

#     cleaned_number = recipient_number.strip()
#     has_plus = cleaned_number.startswith('+')
#     cleaned_number_digits = ''.join(filter(str.isdigit, cleaned_number))

#     if has_plus:
#         final_cleaned_number = '+' + cleaned_number_digits
#     else:
#         final_cleaned_number = cleaned_number_digits

#     if not final_cleaned_number or (has_plus and len(final_cleaned_number) <= 1) or len(cleaned_number_digits) < 4:
#         return f"Error: Invalid phone number format provided or too short ('{recipient_number}' -> '{final_cleaned_number}')."

#     tel_uri = f"tel:{final_cleaned_number}"
#     adb_command_args = ["shell", "am", "start", "-a", "android.intent.action.CALL", "-d", tel_uri]

#     sim_slot_message = ""
#     if sim_slot is not None:
#         try:
#             slot_index = int(sim_slot)
#             if slot_index in [0, 1]:
#                 adb_command_args.extend(["--ei", "com.android.phone.extra.slot", slot_index])
#                 sim_slot_message = f" (attempting to use SIM slot {slot_index + 1})"
#                 logging.info(f"Attempting to specify SIM slot index: {slot_index}")
#             else:
#                 logging.warning(f"Invalid SIM slot index provided: {sim_slot}. Ignoring.")
#                 sim_slot_message = " (invalid SIM slot specified, using default)"
#         except ValueError:
#             logging.warning(f"Invalid SIM slot value provided: {sim_slot}. Must be an integer (0 or 1). Ignoring.")
#             sim_slot_message = " (invalid SIM slot specified, using default)"

#     success, output = run_adb_command(adb_command_args)

#     if success:
#         logging.info(f"ADB command to initiate call to {final_cleaned_number}{sim_slot_message} sent.")
#         base_message = f"Okay, I've sent the command to your Android device to start a call to {final_cleaned_number}{sim_slot_message}."
#         confirmation_needed_message = " Please check your phone screen, you might need to confirm the call"
#         if "error" in output.lower() or "unable to resolve intent" in output.lower():
#              if "com.android.phone.extra.slot" in output.lower():
#                   logging.warning(f"Command sent, but device reported issue resolving SIM slot extra: {output}")
#                   return base_message + confirmation_needed_message + " (Note: SIM selection might not have worked)."
#              else:
#                   return f"Sorry, the command was sent but the device reported an error trying to start the call: {output}"
#         else:
#              return base_message + confirmation_needed_message
#     else:
#         return f"Sorry, I failed to send the call command via ADB. {output}"


# # --- Main Execution Block (Keep As Is - Already uses Google Contacts) ---
# if __name__ == "__main__":
#     # ... (main block code remains unchanged) ...
#     print("--- ADB Call Assistant (Google Contacts Search) ---")
#     # 1. Check ADB device connection
#     print("Checking ADB device connection...")
#     connect_success, connect_output = run_adb_command(["devices"])
#     if not connect_success:
#         print(f"ADB Connection Error: {connect_output}")
#         sys.exit(1)
#     if "unauthorized" in connect_output.lower():
#          print(f"ADB Connection Error: Device unauthorized. Please allow USB debugging on your phone.")
#          sys.exit(1)
#     if not "device" in connect_output.lower():
#          print(f"ADB Connection Error: No authorized device found. Output:\n{connect_output}")
#          sys.exit(1)
#     print("Device connected.")

#     # 2. Get Contact Name or Number
#     target_number = None
#     user_input = input("\nEnter contact name or phone number to call: ").strip()

#     if not user_input:
#         print("No input provided.")
#         sys.exit(1)

#     # Check if input looks like a phone number
#     if len(re.findall(r'\d', user_input)) >= 5 and all(c in '0123456789+-() ' for c in user_input):
#         print("Input looks like a phone number.")
#         target_number = user_input
#         number_source_message = f"Using provided number: {target_number}"
#     else:
#         print("Input looks like a name. Searching Google Contacts...")
#         # --- MODIFIED: Search Google Contacts ---
#         found_number, search_message = get_contact_number_google(user_input)
#         print(search_message) # Print message from search function
#         if found_number:
#             target_number = found_number
#             number_source_message = f"Using number from Google Contacts: {target_number}"
#         else:
#             # Error message already printed
#             sys.exit(1) # Exit if contact/number not found or error occurred
#         # --- End Modification ---

#     # 3. Get SIM Slot Choice (if number was found)
#     selected_sim_slot = None # Default to None (let system decide)
#     if target_number:
#         print(f"\n{number_source_message}")
#         sim_choice = input("Enter SIM slot to use (1 or 2, leave blank for default): ").strip()
#         if sim_choice == '1':
#             selected_sim_slot = 0 # Index 0 for SIM 1
#             print("Attempting to use SIM 1.")
#         elif sim_choice == '2':
#             selected_sim_slot = 1 # Index 1 for SIM 2
#             print("Attempting to use SIM 2.")
#         elif sim_choice: # If user entered something other than 1, 2, or blank
#             print("Invalid SIM choice, using default.")
#         else: # If user left it blank
#             print("Using default SIM slot.")

#         # 4. Make the Call
#         call_result = make_phone_call_adb(target_number, sim_slot=selected_sim_slot) # Use the chosen slot
#         print(f"\nCall Result: {call_result}")

#     else:
#         print("\nCould not determine a phone number to call.")
