# JARVIS AI Assistant

<img width="917" alt="Screenshot UI" src="https://github.com/user-attachments/assets/e1304243-fef7-412e-a8b8-da9939c8ad8a" />


## Project Overview

JARVIS AI is a versatile voice-activated personal assistant designed to perform a variety of tasks through natural language commands. It integrates with multiple services and local system functionalities to provide a seamless user experience. Key capabilities include web browsing and searching, application control, file reading (DOCX, PDF, PPTX, KEY), system monitoring (battery, USB), and Android device control via ADB.

## Features

*   **Voice-Activated Commands**: Interact with Jarvis using natural language.
*   **Web Automation**:
    *   Open websites and specific web pages.
    *   Search Google and YouTube.
    *   Control browser tabs (open, close, switch, refresh, etc.).
    *   Scroll web pages.
*   **Application Control**:
    *   Open and close local applications on Windows, macOS, and Linux.
    *   Close the current active window/tab.
*   **File Interaction**:
    *   Read content from DOCX, PDF, PPTX, and Keynote (.key) files.
    *   Search within PDF documents.
*   **System Monitoring & Alerts**:
    *   Check battery percentage and provide advice.
    *   Monitor charger plug/unplug status.
    *   Detect Pen Drive (USB) connections/disconnections.
    *   Provide battery level alerts.
*   **Android Device Control (via ADB)**:
    *   Make phone calls (with contact search from local CSV or Google Contacts).
    *   End phone calls.
    *   Toggle speakerphone.
    *   Take screenshots.
    *   Check device battery percentage.
    *   Automatic Wi-Fi ADB connection management.
*   **Real-time Information & Chat**:
    *   Leverages Groq API for fast responses and function calling.
    *   General conversational capabilities.
*   **User Authentication**:
    *   Optional face recognition to authenticate the user.
*   **Cross-Platform Support**: Core functionalities aim to work on Windows, macOS, and Linux, with platform-specific commands where necessary.

## Prerequisites

*   Python 3.8 or higher
*   `pip` (Python package installer)
*   **For Android Control (ADB)**:
    *   Android SDK Platform Tools installed and `adb` added to your system's PATH.
    *   USB Debugging enabled on your Android device.
    *   developer mode on your Android device.
*   **For macOS specific features (e.g., Keynote reading, Apple STT)**:
    *   Relevant permissions for automation and microphone access.
*   **For eSpeakNG TTS**:
    *   `espeak-ng` installed on your system.
    *   (Linux): `sudo apt-get install espeak-ng`
    *   (macOS): `brew install espeak-ng`
    *   (Windows): Download from eSpeak NG GitHub

## Setup Instructions

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/Amanhingve/JARVIS-AI.git
    &
    DVD-CD JARVIS AI # copy this DVD-CD project Or your project's root directory name
    cd JARVIS AI # Or your project's root directory name
    ```

2.  **Install Dependencies**:
    It's highly recommended to use a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
    Install the required Python packages:
    ```bash
    pip3 install -r requirements.txt
    ```
    The `setup.py` script primarily handles this `requirements.txt` installation.

3.  **Environment Variables**:
    Create a `.env` file in the project root directory. This file is used to store API keys and user preferences.
    Copy the example below and fill in your actual keys:
    ```env
    # .env
    user=Sir # Your preferred name
    ai_name=Jarvis # Name for the AI assistant

    # API Keys (Obtain these from their respective services)
    GroqAPIKey="YOUR_GROQ_API_KEY"
    cohereAPIKey="YOUR_COHERE_API_KEY"
    # PICOVOICE_ACCESS_KEY="YOUR_PICOVOICE_ACCESS_KEY" # If using Picovoice Porcupine for hotword

    # For Google Contacts integration (adb_call.py)
    GOOGLE_CLIENT_ID="YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET="YOUR_GOOGLE_CLIENT_SECRET"
    ```
    *   **GroqAPIKey**: For fast LLM responses and function calling.
    *   **cohereAPIKey**: For certain NLP tasks like target extraction in `open_closeWebApp.py`.
    *   **GOOGLE\_CLIENT\_ID & GOOGLE\_CLIENT\_SECRET**: For accessing Google Contacts if you choose to use that feature in `Automation/adb_call.py`. You'll need to set up a project in Google Cloud Console, enable the People API, and create OAuth 2.0 credentials.

4.  **Face Authentication (Optional)**:
    If you want to use face authentication:
    *   Ensure you have a webcam connected.
    *   Run the `sample.py` script to capture face samples:
        ```bash
        python3 BRAIN/auth/sample.py
        ```
        Follow the prompts (enter a numeric user ID, e.g., `1`).
    *   Run the `trainer.py` script to train the face recognizer:
        ```bash
        python3 BRAIN/auth/trainer.py
        ```
    *Note: The authentication is currently enabled in `main.py`. You can comment it out if not needed.*

5.  **Local Contacts for ADB Calls (Optional)**:
    If you want to make calls using a local contact list with `Automation/adb_call.py`:
    *   Create a CSV file named `local_contacts.csv` inside the `Data/` directory (`Data/local_contacts.csv`).
    *   The CSV file must have a header row with `Name` and `Number` columns.
    *   Example `Data/local_contacts.csv`:
        ```csv
        Name,Number
        John Doe,+11234567890
        Jane Smith,9876543210
        ```
## Optional Features

6.  **Google Contacts Authentication (for `adb_call.py`)**:
    If you plan to use Google Contacts for making calls via ADB:
    *   The first time `Automation/adb_call.py` (or a function calling it) tries to access Google Contacts, it will initiate an OAuth 2.0 flow.
    *   A browser window will open, asking you to log in and authorize access.
    *   Upon successful authorization, a `token.json` file will be created in the `Automation/` directory. This token will be reused for future sessions.
    *   Ensure your `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in the `.env` file are correct and correspond to an OAuth 2.0 Client ID for a Desktop application with the People API enabled.

## Running Jarvis

Jarvis can be run in two modes:

1.  **Standalone Mode (with Hotword Detection Simulation)**:
    Jarvis will listen for a wake word (e.g., "Jarvis") before processing commands.
    ```bash
    python3 main.py
    ```

2.  **UI Mode (for integration with a separate UI)**:
    This mode bypasses the initial hotword detection and expects input via stdin, typically from another process managing the user interface.
    ```bash
    python3 ui.py --ui-mode
    ```

## Interacting with Jarvis

*   **Activation**:
    *   In **Standalone Mode**: Say the wake word (e.g., "Jarvis" or "Hey Jarvis"). Jarvis will respond with "Yes sir?" indicating it's ready for a command.
    *   In **UI Mode**: Interaction is typically managed by the UI application. `main.py` will expect input directly.
*   **Giving Commands**:
    *   Once activated (or in UI mode), speak your command naturally.
    *   Examples:
        *   "Open Google"
        *   "Search YouTube for Python tutorials"
        *   "What's the battery percentage?"
        *   "Read the PDF document named report.pdf"
        *   "Call John Doe" (if using ADB calling feature)
        *   "Close the current tab"
*   **Exiting**:
    *   Say "exit", "quit", or "bye" to shut down Jarvis.

## Project Structure

```
JARVIS AI/
├── Readme.md                       # Setup Instructions, project overview
├── .env                            # Environment variables (API keys, user settings)
├── main.py                         # Main application script, orchestrator
├── setup.py                        # Script to install dependencies (e.g., runs pip install -r requirements.txt)
├── requirements.txt                # Lists Python package dependencies
├── ENGINE/                         # Package for core input/output engines
│   ├── __init__.py                 # Makes ENGINE a Python package
│   ├── STT/                        # Sub-package for Speech-To-Text modules
│   │   ├── __init__.py             # Makes STT a Python package
│   │   └── apple_stt.py            # Example: STT using Apple's native services
│   └── TTS/                        # Sub-package for Text-To-Speech modules
│       ├── __init__.py             # Makes TTS a Python package
│       ├── eSpeakNG_fast50ms.py    # Example: TTS using eSpeak NG
│       └── TTS_DF.py               # Example: TTS using hi-IN-MadhurNeural
├── BRAIN/                          # Package for AI logic and "intelligence" components
│   ├── __init__.py                 # Makes BRAIN a Python package
│   ├── auth/                       # Sub-package for authentication logic
│   │   ├── __init__.py             # Makes auth a Python package
│   │   ├── recoganize.py           # Authentication logic (e.g., face recognition)
│   │   ├── sample.py               # Script to capture face samples for training
│   │   └── trainer.py              # Script to train the face recognizer model
│   └── ai_chat_res/                # Sub-package for AI chat responses, function calling, and prompts
│       ├── __init__.py             # Makes ai_chat_res a Python package
│       ├── Chatbot.py              # Fallback chatbot logic
│       ├── functions_call.py       # Defines available local functions for the LLM
│       ├── image_gen/              # Sub-package for image generation
│       │   ├── __init__.py         # Makes image_gen a Python package
│       │   └── img_gen.py          # Image generation logic using Hugging Face API
│       ├── stock/                    # Sub-package for stock related functions
│       │   ├── __init__.py         # Makes stock a Python package
│       │   └── stockRealtime.py    # Stock price and chart functions
│       ├── RealtimeSearchEngine_groq.py # Provides context/info to LLM, web search
│       └── system_prompts.py       # System prompts for guiding the LLM
├── Automation/                     # Package for background automation tasks
│   ├── __init__.py                 # Makes Automation a Python package
│   ├── textRead.py                 # Functions for reading various file types (DOCX, PDF, PPTX, KEY)
│   ├── search_in_google.py         # Function for Google search via pywhatkit
│   ├── battery_alert.py            # Script for battery monitoring and alerts
│   ├── check_battery_persentage.py # Function to get battery advice
│   ├── open_closeWebApp.py         # Functions for opening/closing websites and applications
│   ├── adb_call.py                 # Functions for ADB phone control (calls, screenshots, etc.)
│   ├── caption_in_video.py         # Functions for video player control (e.g., VLC, YouTube)
│   ├── pen_drive_plug_check.py     # Script for USB drive (Pen Drive) detection
│   ├── Another_Automation_in_youtube.py # Functions for YouTube specific controls
│   ├── tab_automation.py           # Functions for browser tab automation (open, close, switch, scroll)
│   └── battery_plug_check.py       # Script to monitor charger plug/unplug status
├── Data/                           # Directory for user data, logs, and configuration files
│   ├── DLG.py                      # (Purpose unclear from name, might be dialogs or data loading)
│   ├── ChatLog.json                # Log of conversations with Jarvis
│   ├── local_contacts.csv          # Local contacts for ADB calling feature
│   └── Open_website_D_set.py       # (Purpose unclear, might be dataset for opening websites)
├── USER_INTERFACE/                 # Package for the Graphical User Interface
│   ├── __init__.py                 # Makes USER_INTERFACE a Python package
│   └── ui.py                       # PyQt5 based GUI application script (alternative to standalone mode)
└── .gitignore                      # Specifies intentionally untracked files for Git
```

#Project screenshot

![jarvis ui](https://github.com/user-attachments/assets/f1dd7b48-dc38-4c56-91d4-394bbeb48835)


<img width="917" alt="Screenshot" src="https://github.com/user-attachments/assets/4a76e0e2-df9b-4091-bb89-8d712fa0b9dc" />

<img width="806" alt="Screenshot" src="https://github.com/user-attachments/assets/2772a257-b43b-4980-8a88-e4ff7cb57d08" />

<img width="832" alt="Screenshot" src="https://github.com/user-attachments/assets/42b0c618-b714-40b4-873a-544ec5961cb9" />

<img width="817" alt="Screenshot" src="https://github.com/user-attachments/assets/d98ef8b6-9208-4d48-a995-a796730231d3" />

<img width="1676" alt="Screenshot" src="https://github.com/user-attachments/assets/578981e5-3767-4a62-a907-aca2cd66666d" />
