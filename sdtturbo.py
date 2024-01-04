from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import urllib.request
# headless mode
options = ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome()
driver.get("https://sdxlturbo.ai/")
input_box = driver.find_element("name", "prompt")
input_box.send_keys("A cat wearing a hat")
# Wait until the image has loaded
wait = WebDriverWait(driver, 15)  # wait for maximum time   
image_class = wait.until(EC.presence_of_element_located((By.XPATH, '//img[@alt="Generated"]')))
image_url = image_class.get_attribute("src")
# Download the image
urllib.request.urlretrieve(image_url, "image.jpg")
# Close the browser
driver.quit()
