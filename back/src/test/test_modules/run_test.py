import analysis
import functions
import create_data
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import usability_sim
import sys
import os
import ast
def run_test(url, test_id, user_age, user_literacy, scenarios):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)
    driver.get(url)
    tree = functions.calc_weights(url, driver)

    scenario_results = []
    for keywords in scenarios:
        task_config = usability_sim.TaskConfig(usability_sim.TaskType("search"), None, keywords, 7)
        user_actions = usability_sim.run_simulation(tree, task_config, 1000, float(user_age), 5, float(user_literacy), float(0.1))
        scenario_results.append(user_actions[0])
    data = {i: val for i, val in enumerate(scenario_results)}
    
    analysis.analysis(driver, data, scenarios, test_id, float(user_age), float(user_literacy))
    driver.quit()
    
print(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
run_test(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], ast.literal_eval(sys.argv[5]))
