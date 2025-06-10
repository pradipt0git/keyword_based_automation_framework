# automation_process.py

from modules.selenium_actions import SeleniumActions
from modules.reporting_v2 import RobustReporting
import datetime
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))

from customization import custom_actions as ca  # Now import directly as ca

    
def process_step(testcasename, screen, field, action, xpath, data, driver, reporting: RobustReporting, actions: SeleniumActions, dataset_number=None, get_pass_screenshot=False):
    """
    Process a single automation step.
    Calls the appropriate SeleniumActions method based on the action.
    Records step result, error message, and screenshot (if failed) in step_results.
    """
    import base64
    import traceback
    status = 'pass'
    error_message = ''
    action_lower = str(action).strip().lower() if action else ''
    result = None
    try:
        # Dynamically call custom action if action starts with 'custom-'
        if action and action.startswith("custom-"):
            action_name = action.replace("custom-", "")
            try:
                custom_function = getattr(ca, action_name, None)
                if custom_function:
                    success, message = custom_function(
                        driver, xpath, data, field, None, testcasename
                    )
                    if not success:
                        status = 'fail'
                        error_message = message
                else:
                    status = 'fail'
                    error_message = f"Custom function '{action_name}' not found in custom_actions.py"
            except Exception as e:
                status = 'fail'
                error_message = f"Error calling custom function '{action_name}': {str(e)}"
        else:
            # Map new action names to logic
            if action_lower == 'openurl':
                result = actions.open_url(data)
                status, error_message = extract_status_and_message(result, 'Failed to open URL')
            elif action_lower == 'inputtext':
                result = actions.set_value(xpath, data)
                status, error_message = extract_status_and_message(result, 'Failed to set value')
            elif action_lower == 'getelementtext':
                result = actions.get_value(xpath)
                status, error_message = extract_status_and_message(result, 'Failed to get value')
            elif action_lower == 'assertvalue':
                result = actions.assert_value(xpath, data)
                status, error_message = extract_status_and_message(result, 'Failed to assert value')
            elif action_lower == 'clickelement':
                result = actions.element_click(xpath)
                status, error_message = extract_status_and_message(result, 'Failed to click element')
            elif action_lower == 'scrollpage':
                result = actions.scroll_page()
                status, error_message = extract_status_and_message(result, 'Failed to scroll page')
            elif action_lower == 'cleartext':
                result = actions.clear_text(xpath)
                status, error_message = extract_status_and_message(result, 'Failed to clear text')
            elif action_lower == 'iselementvisible':
                result = actions.is_element_visible(xpath)
                status, error_message = extract_status_and_message(result, 'Failed to check element visibility')
            else:
                reporting.log_info(f"No matching Selenium action for: {action}")
                print(f"[SKIP] No matching Selenium action for: {action}")
                status = 'fail'
                error_message = f"No matching Selenium action for: {action}"
        # Optionally print or log the result
        log_line = (
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"TestCase={testcasename}, Dataset={dataset_number}, Screen={screen}, Field={field}, Action={action}, "
            f"Xpath={xpath}, Data={data}, Status={status}, Message={error_message if error_message else result}"
        )
        # Write to execution_log.txt in the report folder
        report_folder = os.environ.get('CURRENT_REPORT_FOLDER')
        if report_folder:
            log_path = os.path.join(report_folder, 'execution_log.txt')
            with open(log_path, 'a', encoding='utf-8') as logf:
                logf.write(log_line + '\n')
        print(log_line)
    except Exception as e:
        status = 'fail'
        error_message = f"Exception in process_step: {e}\n{traceback.format_exc()}"
        reporting.log_error(error_message)
        print(f"[ERROR] Exception in process_step: {e}")
    
    # Take screenshot if failed or if get_pass_screenshot is True and status is pass
    screenshot_path = ''
    if (status == 'fail' and driver is not None) or (get_pass_screenshot and status == 'pass' and driver is not None):
        try:
            # Save screenshot to file in Screenshots folder inside the report folder
            report_folder = os.environ.get('CURRENT_REPORT_FOLDER')
            if report_folder:
                screenshots_dir = os.path.join(report_folder, 'Screenshots')
                os.makedirs(screenshots_dir, exist_ok=True)
                screenshot_filename = f"{testcasename}_{screen}_{field}_{action}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
                screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
                driver.save_screenshot(screenshot_path)
            else:
                screenshot_path = ''
        except Exception as e:
            screenshot_path = ''
            error_message += f" | Screenshot error: {e}"
    # Prepare and return step result
    return {
        'testcasename': testcasename,
        'dataset number': dataset_number,
        'screen': screen,
        'field': field,
        'action': action,
        'xpath': xpath,
        'data': data,
        'execution_status': status,
        'error message': error_message,
        'screenshot': screenshot_path
    }

def extract_status_and_message(result, default_fail_msg):
    """
    Helper to extract status and error message from a SeleniumActions result.
    Returns (status, error_message).
    """
    if isinstance(result, tuple):
        # Expecting (success, message)
        success, message = result
        if not success:
            return 'fail', message or default_fail_msg
        else:
            return 'pass', ''
    elif isinstance(result, dict):
        if not result.get('success', True):
            return 'fail', result.get('message', default_fail_msg)
        else:
            return 'pass', ''
    elif result is False:
        return 'fail', default_fail_msg
    else:
        return 'pass', ''
