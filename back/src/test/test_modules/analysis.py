from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import random
from Screenshot import Screenshot
import matplotlib.pyplot as plt
import numpy as np
import time as t
import functions
import img_db
import scen_db
import psycopg2

def calc_tasks_completed(data):
    number_of_tasks = len(data.keys()) # число задач
    s = 0 # сумма долей выполнения задач пользователями 
    # расчет доли выполнения задач пользователями 
    # ( потом суммируем и получаем общее "число выполненных задач" для среднего пользователя) 
    for key, value in data.items():
        total_successful = 0
        total = len(value)
        for user in value:
            if user["success"]!=-1:
                total_successful+=1
        s += total_successful/total
        
    tasks_completed = s/number_of_tasks
    return tasks_completed

def calc_errors_in_task (data):
    count=0
    for user in data:
        count+=len(user["clicks"])
        if user["success"]!=-1:
            count-=1
                
    return count/len(data)

def calc_tasks_with_errors(data):
    number_of_tasks = len(data.keys())
    average_errors=0
    for key, value in data.items():
        errors_in_task=0
        for user in value:
            if user["success"]==-1:
                errors_in_task+=1
            elif len(user["clicks"])>1:
                errors_in_task+=1
        average_errors += errors_in_task/len(value)
    
    tasks_with_errors = average_errors/number_of_tasks
    return tasks_with_errors

def calc_task_error_intensity(data):
    errors_in_task=0
    for user in data:
        if user["success"]==-1:
            errors_in_task+=1
        elif len(user["clicks"])>1:
            errors_in_task+=1
    average_errors = errors_in_task/len(data)
    return average_errors

def calc_completion_time(data):
    time_on_task=0
    successful_users=0
    for user in data:
        if user["success"] != -1:
            successful_users += 1
            time_on_task += user["time"][user["clicks"].index(user["success"])]
    if successful_users==0: return 0
    else: return time_on_task/successful_users

def get_heatmap_color(c, a):
    return {'r': min(88,176*(0.5-0.5*c/a)**(1/2)),'g': min(88,176*(0.5*c/a)**(1/2))}
    #return {'r': min(88,176*(1-c/a)),'g': min(88,176*c/a)}

def get_map(driver, clicks, filename):
    total_clicks=0
    for key, value in clicks.items():
        total_clicks+=value

    def rec2(elem):
        children = elem.find_elements(By.XPATH, "./*")
        colors = get_heatmap_color(clicks[elem.id], total_clicks)
        driver.execute_script("arguments[0].style.background = 'rgb("+str(colors['r'])+","+str(colors['g'])+",0)';", elem)
        
        for child in children:
            if(child.tag_name!="script" and child.tag_name!="link"):
                rec2(child)
    
    rec2(body)
    ss = Screenshot(driver)
    ss.capture_full_page(filename)

def create_age_graph(db_data, data, age):
    id = img_db.push(db_data)
    success_all = [0]*91
    toger_all = [0]*91
    ages = np.arange(age-5, age+6, 1)
    for user in data: 
        if user["success"]!=-1:
            success_all[user["age"]]+=1
        toger_all[user["age"]]+=1

    success = success_all[age-5:age+6]
    together = toger_all[age-5:age+6]
    
    for i in range(11):
        success[i]/=together[i]

    plt.plot(ages, success)
    plt.ylim(0,1.1)
    plt.title('Зависимость успеха от возраста пользователя')
    plt.xlabel('Возраст')
    plt.ylabel('Доля успешных пользователей')
    plt.savefig("image_storage/"+str(id)+".png")
    plt.clf()

def create_literacy_graph(db_data, data, literacy):
    id = img_db.push(db_data)
    literacy_vals = np.array([(user['skill']-0.5)*100 for user in data])
    success_vals = np.array([int(user['success']!=-1) for user in data])
    print(literacy_vals)

    bin_edges = np.linspace((literacy-0.6)*100,(literacy-0.4)*100, 11)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    success_rate = []
    for i in range(10):
        mask = (literacy_vals >= bin_edges[i]) & (literacy_vals < bin_edges[i+1])
        if np.any(mask):
            rate = np.average(success_vals[mask])
        else:
            rate = np.nan  # No data in this bin
        success_rate.append(rate)

    plt.plot(bin_centers, success_rate)
    plt.ylim(0,1.1)
    plt.title('Зависимость успеха от технической грамотности пользователя')
    plt.xlabel('Техническая грамотность')
    plt.ylabel('Доля успешных польщователей')
    plt.savefig("image_storage/"+str(id)+".png")
    plt.clf()

def create_heatmap(db_data, driver, data): #----------------------------------------------------------------------------------------------------------------
    id = img_db.push(db_data)
    driver.execute_script('document.documentElement.style.background = "rgb(88,0,0)";')
    body = driver.find_element("tag name", "body")
    t.sleep(10)
    ids=[]
    def rec(elem): 
        ids.append(driver.execute_script('return arguments[0].getAttribute("data-id");', elem))
        children = elem.find_elements(By.XPATH, "./*")
        for child in children: 
            rec(child)
    rec(body)
    
    clicks = dict(zip(ids,[0]*len(ids)))
    for user in data:
        for click_id in user["clicks"]:
            clicks[str(click_id)] += 1
            
    total_clicks=0
    for key, value in clicks.items():
        total_clicks+=value

    def rec2(elem):
        children = elem.find_elements(By.XPATH, "./*")
        colors = get_heatmap_color(clicks[driver.execute_script('return arguments[0].getAttribute("data-id");', elem)], total_clicks)
        driver.execute_script("arguments[0].style.background = 'rgb("+str(colors['r'])+","+str(colors['g'])+",0)'; arguments[0].style.color = 'white';", elem)
        
        for child in children:
            if(child.tag_name!="script" and child.tag_name!="link"):
                rec2(child)
    
    rec2(body)
    ss = Screenshot(driver)
    ss.capture_full_page("image_storage/"+str(id)+".png")

def create_first_click_heatmap(db_data, driver, data): #------------------------------------------------------------------------------------------------------
    id = img_db.push(db_data)
    driver.execute_script('document.documentElement.style.background = "rgb(88,0,0)";')
    body = driver.find_element("tag name", "body")
    t.sleep(10)
    ids=[]
    def rec(elem): 
        ids.append(driver.execute_script('return arguments[0].getAttribute("data-id");', elem))
        children = elem.find_elements(By.XPATH, "./*")
        for child in children: 
            rec(child)
    rec(body)
    
    clicks = dict(zip(ids,[0]*len(ids)))
    
    for user in data:
        clicks[str(user["clicks"][0])] += 1
            
    total_clicks=0
    for key, value in clicks.items():
        total_clicks+=value

    def rec2(elem):
        children = elem.find_elements(By.XPATH, "./*")
        colors = get_heatmap_color(clicks[driver.execute_script('return arguments[0].getAttribute("data-id");', elem)], total_clicks)
        driver.execute_script("arguments[0].style.background = 'rgb("+str(colors['r'])+","+str(colors['g'])+",0)'; arguments[0].style.color = 'white';", elem)
        
        for child in children:
            if(child.tag_name!="script" and child.tag_name!="link"):
                rec2(child)
    
    rec2(body)
    ss = Screenshot(driver)
    ss.capture_full_page("image_storage/"+str(id)+".png")


def analysis(driver, data, scenarios, test_id, age, literacy): #---------------------------------------------------------------------------------------------------------------------
    #for entire test    
    conn = psycopg2.connect("dbname=website_db user=postgres password=50bmg")
    cur = conn.cursor()
    cur.execute('UPDATE test_table SET tc = %s, twe = %s WHERE test_id = %s;', (calc_tasks_completed(data), calc_tasks_with_errors(data), test_id))
    conn.commit()

    for key, value in data.items():
    #for each scenario
        scenario_id = scen_db.push({"keywords": scenarios[key], "eit": calc_errors_in_task(value), "tei": calc_task_error_intensity(value), "ct": calc_completion_time(value), "test_id": test_id})
        create_age_graph({"scenario_id":scenario_id, "content": "Зависимость успеха от возраста пользователя"}, value, int(age))
        #create_age_graph({"scenario_id":scenario_id, "content": "Зависимость успеха от технической грамотности пользователя"}, value)
        create_literacy_graph({"scenario_id":scenario_id, "content": "Зависимость успеха от технической грамотности пользователя"}, value, literacy)
        create_heatmap({"scenario_id":scenario_id, "content": "Тепловая карта"}, driver, value)
        create_first_click_heatmap({"scenario_id":scenario_id, "content": "Тепловая карта первых нажатий"}, driver, value)