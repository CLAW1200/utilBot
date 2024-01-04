from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions

try:
    options = FirefoxOptions()
    options.add_argument("--headless")
    brower = webdriver.Firefox(options=options)

    brower.get('https://pythonbasics.org')
    print(brower.page_source)
finally:
    try:
        brower.close()
    except:
        pass