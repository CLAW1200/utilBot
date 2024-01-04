from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# Path to your ChromeDriver executable
chrome_driver_path = '/path/to/chromedriver'

# Optional: Add any additional options for the Chrome browser
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # Run in headless mode (without opening a browser window)

# Create a service object
service = Service(chrome_driver_path)

# Start the ChromeDriver server
service.start()

# Create a new instance of the Chrome driver
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open a website
driver.get("https://www.example.com")

# Perform any desired actions or tests here

# Close the browser window
driver.quit()

# Stop the ChromeDriver server
service.stop()
