from selenium import webdriver

# Initialize the Chrome WebDriver
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
# options.add_argument('--disable-dev-shm-usage')
# options.add_argument('--remote-debugging-port=9222') 


driver = webdriver.Chrome(options=options)

# Retrieve the capabilities
capabilities = driver.capabilities

# For Chrome:
if 'browserName' in capabilities and capabilities['browserName'] == 'chrome':
    browser_version = capabilities.get('browserVersion', 'Unknown')
    chromedriver_version = capabilities.get('chrome', {}).get('chromedriverVersion', 'Unknown').split(' ')[0]
    print(f"Browser Name: Chrome")
    print(f"Browser Version: {browser_version}")
    print(f"ChromeDriver Version: {chromedriver_version}")

# Close the driver
driver.quit()