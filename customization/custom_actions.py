from modules.globals import global_dict
from modules.selenium_actions import SeleniumActions
import os
from modules.reporting_v2 import RobustReporting

reporting = RobustReporting()

def switch_to_browser_tab(driver, xpath=None, value=None, fieldname=None, pagename=None, teststep=None, testname=None):
    """Switch to a specific browser tab based on the provided value."""
    try:
        tab_index = int(value) if value is not None else 0
        driver.switch_to.window(driver.window_handles[tab_index])
        log_message = f"Switched to browser tab: {tab_index}"
        reporting.log_info(log_message)
        print(log_message)
        return True, log_message
    except Exception as e:
        error_message = f"Failed to switch to browser tab: {str(e)}"
        reporting.log_error(error_message)
        print(error_message)
        return False, error_message

def reload_current_window(driver, xpath=None, value=None, fieldname=None, pagename=None, teststep=None, testname=None):
    """Reload the current browser window."""
    try:
        driver.refresh()  # Refresh the current window
        log_message = "Reloaded the current browser window successfully."
        reporting.log_info(log_message)
        print(log_message)
        return True, log_message
    except Exception as e:
        error_message = f"Failed to reload the current browser window: {str(e)}"
        reporting.log_error(error_message)
        print(error_message)
        return False, error_message
    
def compare_text(driver, xpath=None, value=None, fieldname=None, pagename=None, teststep=None, testname=None):
    """Custom action: Check if data from datasheet (value) matches data present in web element (xpath)."""
    try:
        if not xpath:
            error_message = "No xpath provided for web element."
            reporting.log_error(error_message)
            print(error_message)
            return False, error_message
        # Use SeleniumActions to get value
        actions = SeleniumActions(reporting, driver)
        success, web_val = actions.get_value(xpath)
        expected_val = str(value).strip() if value is not None else ''
        if success and str(web_val).strip() == expected_val:
            log_message = f"Assert passed: Web value '{web_val}' matches expected '{expected_val}'"
            reporting.log_info(log_message)
            print(log_message)
            return True, log_message
        else:
            error_message = f"Assert failed: Web value '{web_val}' does not match expected '{expected_val}'"
            reporting.log_error(error_message)
            print(error_message)
            return False, error_message
    except Exception as e:
        error_message = f"Exception in assert_datasheet_equals_web: {str(e)}"
        reporting.log_error(error_message)
        print(error_message)
        return False, error_message
    
def get_and_store_text(driver, xpath=None, value=None, fieldname=None, pagename=None, teststep=None, testname=None):
    """Custom action: Get text/value from an element using xpath and store/log it with the given fieldname (with $$ prefix)."""
    try:
        if not xpath:
            error_message = "No xpath provided for get_text."
            reporting.log_error(error_message)
            print(error_message)
            return False, error_message
        if not fieldname or not fieldname.startswith('$$'):
            error_message = "Fieldname must be provided and start with '$$' for get_text."
            reporting.log_error(error_message)
            print(error_message)
            return False, error_message
        # Use SeleniumActions to get value
        actions = SeleniumActions(reporting, driver)
        success, result = actions.get_value(xpath)
        if success:
            log_message = f"get_text: Value for {fieldname} is '{result}'"
            reporting.log_info(log_message)
            print(log_message)
            # Store in global_dict for global access
            global_dict[fieldname] = result
            # Optionally, store in reporting.values_dict or similar if needed
            if hasattr(reporting, 'values_dict'):
                reporting.values_dict[fieldname] = result
            return True, result
        else:
            error_message = f"get_text failed for {fieldname}: {result}"
            reporting.log_error(error_message)
            print(error_message)
            return False, error_message
    except Exception as e:
        error_message = f"Exception in get_text: {str(e)}"
        reporting.log_error(error_message)
        print(error_message)
        return False, error_message