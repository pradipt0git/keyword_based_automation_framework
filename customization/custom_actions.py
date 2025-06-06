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