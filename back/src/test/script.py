import requests
from bs4 import BeautifulSoup
from bs4 import NavigableString
import wget
import cssutils
import os
import tinycss2
import logging
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from Screenshot import Screenshot
import sys

def get_map(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)  
    driver.get(url)
    body = driver.find_element("tag name", "body")

    #set all color to red
    
    def rec(elem):
        driver.execute_script("arguments[0].style.background = '#880000';", elem)
        children = elem.find_elements(By.XPATH, "./*")
        for child in children:
            rec(child)
    rec(body)
    print(os.getcwd())
    ss = Screenshot(driver)
    ss.capture_full_page("screenshot_filename.png")
    sys.stdout.flush()

get_map(sys.argv[1])