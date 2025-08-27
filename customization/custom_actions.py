
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
        # Find the element and get its visible value/text
        element = driver.find_element_by_xpath(xpath)
        web_val = ''
        # Try to get text content if visible
        if element.is_displayed():
            # Try .text (for h1, span, div, etc.)
            web_val = element.text.strip() if element.text else ''
            # If .text is empty, try value attribute (for input, textarea)
            if not web_val:
                web_val = element.get_attribute('value')
                web_val = web_val.strip() if web_val else ''
            # If still empty, try innerText (for some edge cases)
            if not web_val:
                try:
                    web_val = driver.execute_script('return arguments[0].innerText;', element)
                    web_val = web_val.strip() if web_val else ''
                except Exception:
                    pass
        expected_val = str(value).strip() if value is not None else ''
        if web_val == expected_val:
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