from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import urllib.request
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
print ("1")
options = FirefoxOptions()
print ("2")
options.add_argument("--headless")
print ("3")
# set path to geckodriver ubuntu
service = Service('/usr/local/bin/geckodriver')
print ("4")
# Set up the Selenium webdriver
driver = webdriver.Firefox(options=options, service=service)
print ("5")
# Navigate to the website
driver.get("https://sdxlturbo.ai/")
print ("6")
input_box = driver.find_element("name", "prompt")
print ("7")
input_box.send_keys("A cat wearing a hat")
print ("8")
# Wait until the image has loaded
wait = WebDriverWait(driver, 15)  # wait for maximum time   
print ("9")
image_class = wait.until(EC.presence_of_element_located((By.XPATH, '//img[@alt="Generated"]')))
print ("10")
image_url = image_class.get_attribute("src")
print ("11")
# Download the image
urllib.request.urlretrieve(image_url, "image.jpg")
print ("12")
# Close the browser
driver.quit()
print ("13")