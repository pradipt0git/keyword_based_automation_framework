# middleware.py
# Dynamically loads and returns the correct automation actions class based on config/framework

import json
import os
from modules.reporting_v2 import RobustReporting

#CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'automation_config.json')
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'automation_config.json')

def get_framework_class(driver=None, browser_type='edge', headless=False):
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    framework = config.get('framework', 'selenium').lower()
    reporting = RobustReporting()
    if framework == 'selenium':
        from modules.selenium_actions import SeleniumActions
        return SeleniumActions(reporting)
    elif framework == 'playwright':
        from modules.playwright_actions import PlaywrightActions
        return PlaywrightActions(reporting, browser_type=browser_type, headless=headless)
    else:
        raise ValueError(f"Unsupported framework: {framework}")
