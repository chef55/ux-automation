from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import random
from Screenshot import Screenshot
import matplotlib.pyplot as plt
import numpy as np
import time as t
import functions

def get_element_ids(elem,arr): 
    arr.append(elem.id)
    children = elem.find_elements(By.XPATH, "./*")
    for child in children: 
        get_element_ids(child, arr)

def generate(driver, tree, user_age, user_literacy, scenarios):

    #get element ids
    body = driver.find_element("tag name", "body")
    t.sleep(10)
    arr=[]
    get_element_ids(body, arr)
    data = dict.fromkeys(scenarios, [])
    print(data)
    #data = {
    #    "1": [],
    #    "2": []
    #}

    for key, value in data.items():
        output = []
        for n in range(1,1000):#users loop
            user_output = {
                "age": random.randrange(14, 70),
                "clicks": [],
                "time": [],
                "success": [],
            }
            n_clicks = random.randrange(1, 15)
            clicks = []
            time = []
            for n in range(0, n_clicks): #clicks loop
                chef = [10, 25, 13, 16, 12,31, 23]
                clicks.append(arr[chef[random.randrange(0, 7)]])
                time.append(random.randrange(1000,300000))
            if (random.randrange(0,10)>=7):
                success = clicks[random.randrange(0,n_clicks)]
            else:
                success=-1
            user_output["clicks"] = clicks
            user_output["time"] = time
            user_output["success"] = success
            output.append(user_output)
        
            
        data[key]=output 
    return data