# custom_component.py
"""
This module allows you to define full custom automation scenarios (e.g., login flows) as reusable functions.
Each function can use the same logging and screenshot mechanism as the main automation flow.
"""

import os
import datetime
from modules.reporting_v2 import RobustReporting
from modules.automation_process import process_step

# Example: Custom login scenario

def run_custom_login(testcasename, actions, driver, reporting, login_screen, username_field, password_field, username, password, login_button_xpath):
    """
    Executes a full login flow and logs each step, saving screenshots and logs just like the main flow.
    """
    step_results = []
    # Step 1: Enter username
    result = process_step(
        testcasename, login_screen, username_field, 'inputtext', username_field, username, driver, reporting, actions,
        get_pass_screenshot=True, testcase_description='Enter Username', validation='', expected_validation='')
    step_results.append(result)
    # Step 2: Enter password
    result = process_step(
        testcasename, login_screen, password_field, 'inputtext', password_field, password, driver, reporting, actions,
        get_pass_screenshot=True, testcase_description='Enter Password', validation='', expected_validation='')
    step_results.append(result)
    # Step 3: Click login button
    result = process_step(
        testcasename, login_screen, 'LoginButton', 'clickelement', login_button_xpath, '', driver, reporting, actions,
        get_pass_screenshot=True, testcase_description='Click Login', validation='', expected_validation='')
    step_results.append(result)
    return step_results

# You can add more custom scenario functions below, following the same pattern.
