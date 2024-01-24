import re
import json
import time
import base64
import tempfile

from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def write_str_to_file(string: str, full_path: Path) -> str:
    with open(full_path, "w") as file:
        file.write(string)

    return full_path


def take_screenshot(url: str = "http://localhost:80"):
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ensure GUI is off
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Set path to chromedriver as per your installation
    service = Service(ChromeDriverManager().install())

    # Choose Chrome Browser
    browser = webdriver.Chrome(service=service, options=chrome_options)

    try:
        browser.get(url)

        # Give time for page to load (optional, depends on the page)
        time.sleep(5)

        # Save screenshot to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        browser.save_screenshot(temp_file.name)
        txt = f"Screenshot saved to {temp_file.name}"
        print(f"\033[38;5;208m{txt}\033[0m")

    finally:
        browser.quit()

    return temp_file.name


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def parse_message(message: str, parser: dict):
    if parser["use_parser"] == False:
        return message

    if parser["type"] == "code":
        language = parser["fields"][0]
        pattern = f"```{language}(.*?)```"

    elif parser["type"] == "json":
        pattern = r"```json\s*(.*?)```"

    regex_obj = re.search(pattern, message, re.DOTALL)
    string_dict = regex_obj.group(1).strip()

    result = string_dict

    if parser["type"] == "json":
        result = json.loads(string_dict)

    return result
