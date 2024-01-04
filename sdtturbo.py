from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import urllib.request
# Initialize the Chrome WebDriver
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
# options.add_argument('--disable-dev-shm-usage')
# options.add_argument('--remote-debugging-port=9222') 
driver = webdriver.Chrome(options=options)
driver.get("https://sdxlturbo.ai/")
input_box = driver.find_element("name", "prompt")
input_box.send_keys("A cat wearing a blue hat")
# Wait until the image has loaded
wait = WebDriverWait(driver, 15)  # wait for maximum time   
image_class = wait.until(EC.presence_of_element_located((By.XPATH, '//img[@alt="Generated"]')))
image_url = image_class.get_attribute("src")
# Download the image
urllib.request.urlretrieve(image_url, "image.jpg")
# Close the browser
driver.quit()
