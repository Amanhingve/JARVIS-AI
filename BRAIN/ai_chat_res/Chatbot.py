import sys
import os
# Add the project root to Python path when running directly
if __name__ == '__main__':
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
from BRAIN.ai_chat_res.RealtimeSearchEngine_groq import RealTimeSearchEngine

# Load environment variables from .env file
env_vars = dotenv_values(".env")

# Access environment variables
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# Initialize an empty list to store chat messages.
messages = []

# Define a system message that provides context to the AI chatbot about its role and behavior.
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI voice assistant named {Assistantname} which also has real-time up-to-date information from the internet.
You are {Assistantname}, an AI assistant created to help {Username} with various tasks and provide information.
Your primary goal is to assist {Username} in a friendly and efficient manner.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
You should always be polite, informative, and helpful.
### **Rules for Interaction:**
1. **Professionalism**  
   - Provide answers in a professional manner, ensuring proper grammar, punctuation, and clarity.  
   - Always use full stops, commas, and question marks correctly.  
   - Do not add unnecessary context—just answer the query based on provided data.
2. **Language Handling:**
   - If the user asks in **English**, reply in **English**.
   - If the user asks in **Hindi**, reply in **Hindi using English script** (Hinglish).
   - If the user asks something like **"What is X? in Hindi"**, reply in **Hindi using English script** (Hinglish).
3. **Response Customization**
    -Do not tell created until I ask, do not talk too much, just answer the question.
   - If the user asks **"Aapko kisne banaya?"** or **"Who created you?"**, reply:  
     `"Mujhe {Username} ne banaya hai. Unhone mujhe AI aur NLP (Natural Language Processing) ka use karke develop kiya hai."`  
   - If the user asks the time, do not provide it unless explicitly requested.  
   - Keep answers clear, precise, and relevant to the query.
4. **Capabilities:** 
    -- I can assist you in many ways! Here’s what I can do for you:  

    🔹 **Answer Questions** → I can provide information on various topics.  
    🔹 **Real-Time Updates** → I can fetch the latest news, weather, and live data.  
    🔹 **Open & Close Apps** → I can open or close websites and applications for you.  
    🔹 **Play Music & Videos** → I can play songs, videos, and search YouTube.  
    🔹 **Set Reminders** → I can remind you about important tasks and events.  
    🔹 **Control System Settings** → I can adjust volume, brightness, and more.  
    🔹 **Generate Images** → I can create AI-generated images based on your descriptions.  
    🔹 **Perform Google & YouTube Searches** → I can find information instantly.  
    ✨ Just tell me what you need, and I’ll handle it! ✨  
"""

# A list of system instructions to be sent to the AI chatbot
SystemChatBot = [{
    "role": "system",
    "content": System
}]

# Attempt to load chat history from a JSON file.
try:
    with open(r"Data/ChatLog.json", "r") as f:
        messages = load(f)
except FileNotFoundError:
    # if the file doesn't exist, create an empty JSON file to store chat log.
    with open(r"Data/ChatLog.json", "w") as f:
        dump([], f)

# Function to get real-time information
def Information():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")
    data = f"User this Real-time information if needed:\n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hours, {minute} minutes, {second} seconds.\n"
    return data

# Function to modify the answer to remove empty lines
def AnswerModifier(Answer):
    lines = Answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    modified_Answer = "\n".join(non_empty_lines)
    return modified_Answer

# Function to get a response from the AI
def ChatBot(Query):
    """
    Function to get a response from the AI chatbot.
    """
    global messages
    try:
        # Load existing chat history/log
        chat_log_path = r"Data/ChatLog.json"
        if os.path.exists(chat_log_path):
            with open(chat_log_path, "r") as f:
                messages = load(f)
        else:
            messages = []

        messages.append({"role": "user", "content": Query})

        # Get real-time information
        real_time_info = Information()

        # Prepare the initial message set for AI response
        completion_messages = (
            SystemChatBot +
            [{"role": "system", "content": real_time_info}] +
            messages
        )

        # Get response from the AI model
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=completion_messages,
            max_tokens=2089,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )

        # Process AI response
        Answer = "".join(chunk.choices[0].delta.content for chunk in completion if chunk.choices[0].delta.content)
        Answer = Answer.replace("</s>", "").strip()

        # **Check if AI response is empty or not relevant**
        if not Answer or "I don't know" in Answer or "I'm not sure" in Answer:
            print("Using RealTimeSearchEngine for accurate data...")
            real_time_response = RealTimeSearchEngine(Query)
            Answer = real_time_response if real_time_response else "Sorry, I couldn't find relevant data."

        messages.append({"role": "assistant", "content": Answer})

        # Save updated chat history/log
        with open(chat_log_path, "w") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(Answer)

    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred while processing your request."

# Example usage
# if __name__ == "__main__":
#     try:
#         while True:
#             user_input = input(f"{Username}: ")
#             if user_input.lower() in ["exit", "quit"]:
#                 break
#             print(ChatBot(user_input))
#     except KeyboardInterrupt:
#         print("\nuser stopped the program")