import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logging.getLogger('selenium').setLevel(logging.WARNING)

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--log-level=3')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')

chrome_service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
driver.get("https://tts.5e7en.me/")
# driver.get("https://ttsmp3.com/")

def speak(text):
    try:
        element_to_click = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="text"]'))
        )
        element_to_click.click()
        element_to_click.send_keys(text)
        print(text)
        sleep_duration = min(0.1 * len(text), 5)
        button_to_click = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="button"]'))
        )
        button_to_click.click()

        time.sleep(sleep_duration)

        element_to_click.clear()

        # time.sleep(sleep_duration)
        # element_to_click.send_keys(Keys.RETURN)
    except Exception as e:
        print(e)

    # driver.find_element(By.ID, "input").clear()
    # driver.find_element(By.ID, "input").send_keys(text)
    # driver.find_element(By.ID, "input").send_keys(Keys.RETURN)
    # driver.find_element(By.ID, "input").clear()
    # driver.find_element(By.ID, "input").send_keys(Keys.RETURN)
    time.sleep(2)

# speak("Hello")
# speak("How are you?")
# # speak("I am fine")
# # speak("What is your name?")
# speak("My name is Jarvis")