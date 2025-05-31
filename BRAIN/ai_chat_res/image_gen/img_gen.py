# img_gen.py
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os
import logging
from PIL import Image
import io
from typing import Union
import time
import sys
import subprocess
import re # Import re for filename sanitization

# Configure logging with timestamps
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# Directory to save generated images (relative to this script's location)
IMAGE_OUTPUT_DIR = "generated_images_api"
# API Token Environment Variable Name
API_TOKEN_ENV_VAR = "HUGGING_FACE_TOKEN" # Changed to match previous successful run

# --- Get API Token from Environment ---
hugginapikey = os.getenv(API_TOKEN_ENV_VAR)
if not hugginapikey:
    error_msg = (
        f"Error: HF API token not found in '{API_TOKEN_ENV_VAR}'. "
        "Please set it in .env or your environment."
    )
    logging.error(error_msg)
    print(error_msg)
    exit(1)
logging.info("Hugging Face API token loaded.")

# --- Initialize the InferenceClient ---
try:
    client = InferenceClient(token=hugginapikey)
    logging.info("InferenceClient initialized.")
except Exception as e:
    logging.error(f"Error initializing InferenceClient: {e}")
    print(f"Error initializing client: {e}")
    exit(1)

# --- Helper function for filenames ---
def sanitize_filename(text):
    """Basic sanitization to create a safe filename from text."""
    text = re.sub(r'[^\w\-_\. ]', '_', text) # Remove invalid chars
    text = text.strip().replace(' ', '_')   # Replace spaces
    # Limit length to avoid issues with long filenames
    return text[:80] # Limit length (adjust as needed)

# --- MODIFIED Function to Generate and Save Image, Returns Path ---
def generate_and_save_image(
    prompt: str,
    model: str = "stabilityai/stable-diffusion-xl-base-1.0"
) -> str:
    """
    Generates an image using the Hugging Face Inference Client, saves it
    to a specific directory with a unique name, and returns the file path.

    Args:
        prompt (str): The text prompt for image generation.
        model (str): The model ID to use for generation.

    Returns:
        str: Full path to the saved image file on success, or an error message string on failure.
    """
    print(f"[1/4] Prompt received: '{prompt}'")
    start_req = time.time()
    print("[2/4] Sending request to Hugging Face Inference API...")
    try:
        # Inference
        image: Image.Image = client.text_to_image(prompt, model=model)
        duration_req = time.time() - start_req
        logging.info(f"Inference completed in {duration_req:.2f} seconds.")
        print(f"[3/4] API response received in {duration_req:.2f}s. Preparing to save...")

        # --- Save the image ---
        start_save = time.time()

        # 1. Define output directory path (relative to this script)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_output_dir = os.path.join(script_dir, IMAGE_OUTPUT_DIR)

        # 2. Create the directory if it doesn't exist
        os.makedirs(full_output_dir, exist_ok=True)

        # 3. Create a unique filename
        safe_prompt = sanitize_filename(prompt)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_prompt}_{timestamp}.png"
        filepath = os.path.join(full_output_dir, filename)

        # 4. Save the PIL Image object directly
        image.save(filepath)

        duration_save = time.time() - start_save
        logging.info(f"Image saved to '{filepath}' in {duration_save:.2f} seconds.")
        print(f"[4/4] Image saved to '{filepath}' in {duration_save:.2f}s.")

        return filepath # Return the full path to the saved image

    except Exception as e:
        # Log the full error with traceback for debugging
        logging.error(f"Error during image generation or saving: {e}", exc_info=True)
        # Provide a user-friendly error message
        error_msg = f"Error during image generation or saving: {type(e).__name__} - {e}"
        print(error_msg)
        return error_msg # Return the error message string

# # --- Example Usage (if run directly) ---
# if __name__ == "__main__":
#     user_prompt = input("Enter prompt: ")
#     # Call the function which now saves the file and returns the path
#     result_path_or_error = generate_and_save_image(user_prompt)

#     # Check if the result is a path (success) or an error message
#     if not result_path_or_error.startswith("Error:"):
#         print(f"Image generation successful. File saved at: {result_path_or_error}")

#         # --- Attempt to open the saved image ---
#         print(f"Attempting to open '{result_path_or_error}'...")
#         try:
#             # Use the returned path directly
#             absolute_path = os.path.abspath(result_path_or_error)
#             if sys.platform == "win32":
#                 os.startfile(absolute_path)
#             elif sys.platform == "darwin":
#                 subprocess.call(["open", absolute_path])
#             else:
#                 subprocess.call(["xdg-open", absolute_path])
#         except FileNotFoundError:
#              print(f"Error: Could not find command to open the image ('open' or 'xdg-open'). Please open '{result_path_or_error}' manually.")
#         except Exception as e_open:
#             print(f"Error opening image: {e_open}")
#         # --- End attempt to open ---

#     else:
#         # The result is an error message string
#         print(f"Image generation failed: {result_path_or_error}")



