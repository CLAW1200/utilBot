import time
from selenium import webdriver
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common.keys import Keys

opts = FirefoxOptions()
opts.add_argument("--headless")
browser = webdriver.Firefox(options=opts)
browser.get('https://google.com/')
print('Title: %s' % browser.title)
time.sleep(2)
browser.quit()