import os
# from tkinter import XView
from googlesearch import search
# from googleapiclient.discovery import build
from groq import Groq
from json import load, dump
import requests
from dotenv import dotenv_values
import yfinance as yf
import plotly.graph_objects as go
# import pandas as pd
# from prophet import Prophet
import re  # Import regular expression module
from duckduckgo_search import DDGS
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
# import datetime  # Ensure the datetime module is imported



# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# Initialize Groq client
groq_client = Groq(api_key=GroqAPIKey)

# System prompt
System = f"""You are {Assistantname}, an AI assistant with real-time capabilities. Follow these rules:
1. Provide current information using the provided search results and real-time data
2. Format responses professionally with proper punctuation
3. For Hindi queries, respond in Hinglish (Hindi in English script)
4. Always reference the latest information from the search results
5. Provide answers in a professional manner, ensuring proper grammar, punctuation, and clarity
6. Always use full stops, commas, and question marks correctly
7. Do not add unnecessary context—just answer the query based on provided data
8. If the user asks in English, reply in English
9. If the user asks in Hindi, reply in Hindi using English script (Hinglish)
10. If the user asks something like \"What is X? in Hindi\", reply in Hindi using English script (Hinglish)"""

SYSTEM_PROMPT = f"""You are {Assistantname}, an AI assistant with real-time capabilities. Rules:
1. Provide current information using search results and real-time data
2. Format responses professionally with proper punctuation
3. For Hindi queries, respond in Hinglish (Hindi in English script)
4. Always reference latest information from search results
5. Handle stock prices with .NS suffix for Indian companies"""

# Load chat history
try:
    with open(r"Data/ChatLog.json", "r") as f:
        ChatLog = load(f)
except FileNotFoundError:
    with open(r"Data/ChatLog.json", "w") as f:
        ChatLog = []
        dump(ChatLog, f)

# Function to get real-time information from the internet using Google
def GoogleSearch(query):
    try:
        results = list(search(query, num_results=5))
        Answer = f"The search results for '{query}' are:\n[start]\n"
        for result in results:
            Answer += f"Title: {result}\n"
            Answer += f"URL: {result}\n\n"
            Answer += f"Description: {result}\n\n"
            Answer += f"Snippet: {result}\n\n"
        Answer += "[end]"
        return Answer
    except Exception as e:
        return f"The search results for '{query}' are:\n[start]\nNo results found. Error: {e}[end]"
    
# Function to get real-time information from the internet using DuckDuckGo
def perform_ddg_search(query: str, max_results: int = 10) -> str:
    """Get search results from DuckDuckGo"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return "\n".join([f"Title: {res['title']}\nURL: {res['href']}" for res in results])
    except Exception as e:
        return f"Search error: {str(e)}"

# Function to extract stock symbol
# def extract_stock_symbol(text):
#     # Regular expression pattern to match common stock symbol patterns (e.g., TATA.NS, TATA MOTORS, AAPL)
#     pattern = r"\b([A-Z]+(?:\.[A-Z]+)?)\b"

#     # Find all matches
#     matches = re.findall(pattern, text)

#     # Filter out short symbols (e.g. 'OF')
#     filtered_matches = [match for match in matches if len(match) > 1]

#     if filtered_matches:
#         return filtered_matches[-1]  # Return the last matched symbol (most likely the correct one)
#     return None

# Function to get stock price
# def get_stock_price(stock_symbol):
#     try:
#         stock = yf.Ticker(stock_symbol)
#         price = stock.history(period="1d")["Close"].iloc[-1]
#         return f"{stock_symbol} ka stock price hai: ${price:.2f}"
#     except (KeyError, IndexError, ValueError) as e:
#         return f"Stock price fetch nahi ho saka. Yeh ho sakta hai ki '{stock_symbol}' ek valid stock ticker na ho, ya phir stock market bandh ho. Error: {e}"
#     except Exception as e:
#         return f"Stock price fetch nahi ho saka. Error: {e}"
    
# Function to get stock price using Google Finance API
def get_stock_price_google(query):
    try:
        # Extract the stock name from the query
        stock_name_match = re.search(r"stock price of (.*)", query, re.IGNORECASE)
        if stock_name_match:
            stock_name = stock_name_match.group(1).strip()
        else:
             stock_name = query
        
        # Replace spaces with '+' for the Google Finance URL
        stock_name_for_url = stock_name.replace(" ", "+")
        
        url = f"https://www.google.com/finance/quote/{stock_name_for_url}"

        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        price_tag = soup.find('div', class_='YMlKec fxKbKc')

        if price_tag:
            price = price_tag.text
            return f"{stock_name} ka stock price hai: {price}"
        else:
            return f"Stock price fetch nahi ho saka. Yeh ho sakta hai ki '{stock_name}' ek valid stock ticker na ho, ya phir stock market bandh ho."
    except Exception as e:
        return f"Stock price fetch nahi ho saka. Error: {e}"
    
def handle_stock_query(user_query: str) -> str:
    """End-to-end stock price handling"""
    try:
        symbol = extract_stock_symbol_groq(user_query)
        if not validate_stock_symbol(symbol):
            return "Please provide a valid stock name. For Indian stocks, try adding 'India' or 'NSE'."
        return get_stock_price(symbol)
    except Exception as e:
        return f"Stock query failed: {str(e)}"
    
def get_web_results(query: str) -> str:
    """Combine multiple search sources"""
    try:
        google_results = "\n".join(list(search(query, num_results=3)))
        ddg_results = perform_ddg_search(query)
        return f"Google Results:\n{google_results}\n\nDuckDuckGo Results:\n{ddg_results}"
    except Exception as e:
        return f"Search error: {str(e)}"

def generate_ai_response(query: str, context: str) -> str:
    """Generate response using Groq AI"""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Query: {query}\n\nContext:\n{context}"}
            ],
            temperature=0.7,
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI response generation failed: {str(e)}"
 
# def extract_stock_symbol(text):
#     """
#     Extract stock symbol from text, adding .NS suffix for Indian stocks.
#     """
#     # Common Indian stock suffixes
#     indian_suffixes = ['.NS', '.BO']
    
#     # If contains "TATA MOTORS" or similar, format it properly
#     if "TATA MOTORS" in text.upper():
#         return "TATAMOTORS:NSE"
    
#     # Regular expression to match stock symbols
#     pattern = r"\b([A-Z]+(?:\.[A-Z]+)?)\b"
#     matches = re.findall(pattern, text.upper())
    
#     if matches:
#         symbol = matches[-1]  # Take the last match
#         # Add .NS suffix for Indian stocks if not present
#         if not any(suffix in symbol for suffix in indian_suffixes):
#             symbol += ":NSE"
#         return symbol
#     return None

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

# Function to extract stock symbol using Groq AI
def extract_stock_symbol_groq(user_query: str) -> str:
    """Find accurate stock symbol using AI and web search"""
    try:
        # First try to extract symbol using Groq AI
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": f"""Extract ONLY the stock symbol from: '{user_query}'. 
                Add .NS for Indian stocks. Examples: 
                'Tata Motors' → TATAMOTORS.NS
                Return ONLY the symbol"""
            }],
            temperature=0.1,
            max_tokens=50,
            top_p=1,
        )
        raw_symbol = response.choices[0].message.content.strip().upper()
        
        # Clean special characters
        symbol = re.sub(r"[^A-Z0-9.:]", "", raw_symbol)
        
        # Validate symbol
        if validate_stock_symbol(symbol):
            return symbol
            
        # If AI gives wrong symbol, perform web search
        # search_results = get_web_results(f"{user_query} stock symbol")
        # Alternatively, you can use perform_ddg_search
        # search_results = perform_ddg_search(f"{user_query} stock symbol yahoo finance", max_results=3)
        search_results = GoogleSearch(f"{user_query} stock symbol yahoo finance")
        symbol_pattern = r"\b([A-Z]{3,15}(\.NS)?)\b"
        matches = re.findall(symbol_pattern, search_results)
        
        if matches:
            for match in matches:
                if validate_stock_symbol(match[0]):
                    return match[0]
        
        return raw_symbol  # Fallback to AI's symbol if nothing found
        
    except Exception as e:
        raise ValueError(f"Could not find symbol: {str(e)}")
    

def validate_stock_symbol(symbol: str) -> bool:
    """Improved symbol validation"""
    try:
        return yf.Ticker(symbol).history(period="1d").shape[0] > 0
    except:
        return False
    
def get_stock_price(symbol: str) -> str:
    """Get current stock price with proper formatting"""
    try:
        stock = yf.Ticker(symbol)
        price = stock.fast_info["last_price"]
        
        # Formatting for Indian stocks
        # if ".NS" in symbol:
        #     return f"Current {symbol} Price: ₹{price:,.2f}"
        return f"Current {symbol} Price: ${price:,.2f}"
    except Exception as e:
        return f"Price check failed: {str(e)}"

# # Function to plot stock chart
def plot_stock_chart(stock_name):
    try:
        stock = yf.Ticker(stock_name)
        df = stock.history(period="1mo")

        # Extract the latest date and price and time
        latest_date = df.index[-1].strftime("%Y-%m-%d")
        latest_price = df["Close"].iloc[-1]
        # Get the current system time in 12-hour format
        current_time = datetime.now().strftime("%I:%M:%S %p")
        # latest_time = df.index[-1].strftime("%H:%M:%S")

        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="Price"))
        fig.update_layout(title=f"{stock_name} Stock Price Chart   price: ${latest_price:.2f}", xaxis_title=f"Date: {latest_date} Time: {current_time} current price: ${latest_price:.2f}", yaxis_title="Price", template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)

        fig.show()
        return f"📈 Real-time chart for {stock_name} is being displayed!\ncurent time: {current_time}\nLatest Date: {latest_date}\nLatest Price: ${latest_price:.2f}"
    except (KeyError, IndexError, ValueError) as e:
        return f"Could not plot chart for {stock_name}. Yeh ho sakta hai ki '{stock_name}' ek valid stock ticker na ho, ya phir stock market bandh ho. Error: {e}"
    except Exception as e:
        return f"Could not plot chart for {stock_name}. Error: {e}"

# Function to predict stock trends
# def predict_stock(stock_name):
#     try:
#         stock = yf.Ticker(stock_name)
#         df = stock.history(period="6mo")

#         df = df.reset_index()
#         df = df.rename(columns={"Date": "ds", "Close": "y"})

#         model = Prophet()
#         model.fit(df)

#         future = model.make_future_dataframe(periods=30)
#         forecast = model.predict(future)

#         return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
#     except (KeyError, IndexError, ValueError) as e:
#         return f"Could not predict stock for {stock_name}. Yeh ho sakta hai ki '{stock_name}' ek valid stock ticker na ho, ya phir stock market bandh ho. Error: {e}"
#     except Exception as e:
#         return f"Could not predict stock for {stock_name}. Error: {e}"

# Function to modify the answer
def AnswerModifier(Answer):
    lines = Answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    return "\n".join(non_empty_lines)

# from datetime import datetime  # Correctly import the datetime class

# def Information():
#     """
#     Function to fetch and return current date and time information.
#     """
#     current_date_time = datetime.now()  # Correct usage of datetime
#     day = current_date_time.strftime("%A")
#     date = current_date_time.strftime("%d")
#     month = current_date_time.strftime("%B")
#     year = current_date_time.strftime("%Y")
#     hour = current_date_time.strftime("%H")
#     minute = current_date_time.strftime("%M")
#     second = current_date_time.strftime("%S")
#     data = f"User this Real-time information if needed:\n"
#     data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
#     data += f"Time: {hour} hours, {minute} minutes, {second} seconds.\n"
#     return data


# Function to get chatbot response
def get_stock_real_time_info(prompt):
    global messages

    with open(r"Data/ChatLog.json", "r") as f:
        messages = load(f)

    messages.append({"role": "user", "content": f"{prompt}"})

    # if "stock" in prompt.lower() or "price" in prompt.lower():
    #     # stock_symbol = extract_stock_name(prompt)
    #     stock_Name = prompt
    #     if stock_Name:
    #         return get_stock_price(stock_Name)
    #     else:
    #         return "Please provide a valid stock ticker."

    # Check for stock price related queries
    # if any(keyword in prompt.lower() for keyword in ["price", "stock", "share"]):
    #     stock_symbol = extract_stock_symbol(prompt)
    #     if stock_symbol:
    #         return get_stock_price(stock_symbol)
    #     else:
    #         return "Please provide a valid stock ticker. For Indian stocks, you can try adding .NS (e.g., TATAMOTORS.NS)"
    # return get_stock_price(prompt)

    # if any(keyword in prompt.lower() for keyword in ["price", "stock", "share"]):
    #     stock_Name = get_stock_price_google(prompt)
    #     return stock_Name
    
    # Check for stock price related queries
    if any(keyword in prompt.lower() for keyword in ["price", "stock", "share"]):
        stock_symbol = extract_stock_symbol_groq(prompt)
        # if stock_symbol:
        return get_stock_price(stock_symbol)
        # else:
        #     return "Please provide a valid stock ticker. For Indian stocks, you can try adding .NS (e.g., TATAMOTORS.NS)"


    # Check for stock chart related queries)
    if "chart" in prompt.lower():
        # stock_symbol = extract_stock_symbol(prompt)
        stock_symbol = extract_stock_symbol_groq(prompt)
        if stock_symbol:
            return plot_stock_chart(stock_symbol)
        else:
            return "Please provide a valid stock ticker."
      

    # if "predict" in prompt.lower():
    #     # stock_symbol = extract_stock_symbol(prompt)
    #     stock_Name = prompt
    #     if stock_Name:
    #         return predict_stock(stock_Name)
    #     else:
    #         return "Please provide a valid stock ticker."

    # search_results = GoogleSearch(prompt)
    # search_resultsddg = perform_ddg_search(prompt)

    # stock results respones
    completion_messages = [{"role": "system", "content": System},
                           {"role:": "system", "content": Information()}
                           ]

    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=completion_messages,
        temperature=0.7,
        max_tokens=2048,
        top_p=1,
        stream=True,
        stop=None
    )

    Answer = ""
    for chunk in completion:
        if chunk.choices[0].delta.content is not None:
            Answer += chunk.choices[0].delta.content

    messages.append({"role": "assistant", "content": Answer.strip()})

    with open(r"Data/ChatLog.json", "w") as f:
        dump(messages, f, indent=4)

    return AnswerModifier(Answer)

# def perform_ddg_search(query: str, max_results: int = 10) -> None:
#     """
#     Performs a DuckDuckGo search and prints the results.
    
#     Args:
#         query (str): The search query.
#         max_results (int): The maximum number of results to return. Defaults to 10.
#     """
#     with DDGS() as ddgs:
#         results = list(ddgs.text(query, max_results=max_results))
#         for result in results:
#             print(f"Title: {result.get('title')}")
#             print(f"Link: {result.get('link')}")
#             print("-" * 40)

# Main function
if __name__ == "__main__":
    try:
        while True:
            prompt = input("Enter your query: ")
            print(get_stock_real_time_info(prompt))
            
            # Perform a DuckDuckGo search
            # print(perform_ddg_search(prompt))
    except KeyboardInterrupt:
        print("\nuser stopped the program")
