import time
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def take_screenshot(url):
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
        print(f"Screenshot saved to {temp_file.name}")

    finally:
        browser.quit()

    return temp_file.name

# Example usage
url = "http://localhost:80"
screenshot_path = take_screenshot(url)
print(f"Screenshot taken and stored at: {screenshot_path}")


import base64
import requests

# OpenAI API Key
api_key = "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"

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

# Path to your image
image_path = screenshot_path

# Getting the base64 string
base64_image = encode_image(image_path)

headers = {
  "Content-Type": "application/json",
  "Authorization": f"Bearer {api_key}"
}

payload = {
  "model": "gpt-4-vision-preview",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Give some Feedback for this frontend, what do you like and what do you dislike in regards to the aesthetics, layout and colors? If there is nothing you dislike, just say 'Design is good'"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image}"
          }
        }
      ]
    }
  ],
  "max_tokens": 300
}

response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

print(response.json())