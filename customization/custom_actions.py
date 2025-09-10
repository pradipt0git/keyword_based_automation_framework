from modules.globals import global_dict
from modules.selenium_actions import SeleniumActions
import os
from modules.reporting_v2 import RobustReporting
import time

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
    
def check_n_goto_next_page_get_and_store_acc_no(driver, xpath=None, value=None, fieldname=None, pagename=None, teststep=None, testname=None):
    """Custom action: Check if xpath present in the page, not found then click on next page icon of table to go to next pagination and check again until it find or pagination ends (next page not clickable), if finally not found then mark as failed."""
    try:
        if not xpath:
            error_message = "No xpath provided for web element."
            reporting.log_error(error_message)
            print(error_message)
            return False, error_message
        
        #in inner recursive function check xpath and continue to next page if not found, if found return xpath of the parent td element
        def check_and_navigate(driver, xpath, max_pages=10):
            actions = SeleniumActions(reporting, driver)
            for page in range(max_pages):
                #when _find_element returns None, then continue to next page                
                element = actions._find_element(xpath)
                if element:
                    return True, element
                # Try to click on next page button/icon
                next_page_xpath = "//a[contains(@class, 'next') or contains(text(), 'Next')]"
                next_page_element = actions._find_element(next_page_xpath)
                if next_page_element and next_page_element.is_enabled():
                    next_page_element.click()
                    time.sleep(2)  # Wait for page to load
                else:
                    break
            return False, None
        
        success, element = check_and_navigate(driver, xpath)
        if success and element:
            #without getting xpath get the parent td element directly
            parent_td_element = element.find_element("xpath", "./ancestor::td")
            #get a span inside that td with class - ng-star-inserted
            span_element = parent_td_element.find_element("xpath", ".//span[contains(@class, 'ng-star-inserted')]")
            if span_element:
                #when found get the text and store in global_dict with fieldname as key
                text_value = span_element.text
                if fieldname and fieldname.startswith('$$'):
                    global_dict[fieldname] = text_value
                    log_message = f"check_n_goto_next_page_get_and_store_acc_no: Found value '{text_value}' for {fieldname}"
                    reporting.log_info(log_message)
                    print(log_message)
                    return True, log_message
                else:
                    error_message = "Fieldname must be provided and start with '$$' for storing value."
                    reporting.log_error(error_message)
                    print(error_message)
                    return False, error_message
            else:
                error_message = "Span element with class 'ng-star-inserted' not found inside parent td."
                reporting.log_error(error_message)
                print(error_message)
                return False, error_message
        else:
            error_message = f"Element not found for xpath: {xpath} after navigating pages."
            reporting.log_error(error_message)
            print(error_message)
            return False, error_message

    except Exception as e:
        error_message = f"Exception in assert_datasheet_equals_web: {str(e)}"
        reporting.log_error(error_message)
        print(error_message)
        return False, error_message
    
def zoomin(driver, xpath=None, value=None, fieldname=None, pagename=None, teststep=None, testname=None):
    """Custom action: press ctrl + at browser level."""
    try:
        import pyautogui
        pyautogui.keyDown('ctrl')
        pyautogui.press('+')

        log_message = "Zoomed in the browser view."
        reporting.log_info(log_message)
        print(log_message)
        return True, log_message
    except Exception as e:
        error_message = f"Failed to zoom in the browser view: {str(e)}"
        reporting.log_error(error_message)
        print(error_message)
        return False, error_message

def zoomout(driver, xpath=None, value=None, fieldname=None, pagename=None, teststep=None, testname=None):
    """Custom action: press ctrl - at browser level."""
    try:
        import pyautogui
        pyautogui.keyDown('ctrl')
        pyautogui.press('-')

        log_message = "Zoomed out the browser view."
        reporting.log_info(log_message)
        print(log_message)
        return True, log_message
    except Exception as e:
        error_message = f"Failed to zoom out the browser view: {str(e)}"
        reporting.log_error(error_message)
        print(error_message)
        return False, error_message