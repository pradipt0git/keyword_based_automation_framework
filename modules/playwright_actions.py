# Add initiatedriver function for Playwright compatibility
def initiatedriver(browser='msedge', headless=True):
    from playwright.sync_api import sync_playwright
    playwright = sync_playwright().start()
    browser_obj = getattr(playwright, browser).launch(headless=headless)
    context = browser_obj.new_context()
    page = context.new_page()
    # Return a tuple for compatibility: (playwright, browser_obj, context, page)
    return page
# playwright_actions.py
# This module contains the PlaywrightActions class, which provides methods to interact with web elements using Playwright.

from modules.reporting_v2 import RobustReporting
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import os

from modules.automation_interface import AutomationActionsInterface

class PlaywrightActions(AutomationActionsInterface):
    def __init__(self, reporting: RobustReporting, driver=None, browser_type='msedge', headless=False):
        self.reporting = reporting
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.driver = self.page
        os.makedirs('Reports', exist_ok=True)

    def open_url(self, url):
        try:
            self.page.goto(url)
            self.reporting.log_info(f"Opened URL: {url}")
            return True, None
        except Exception as e:
            error_message = f"Failed to open URL {url}: {str(e)}"
            self.reporting.log_error(error_message)
            return False, error_message

    def set_value(self, selector, value):
        try:
            self.page.fill(selector, str(value))
            self.reporting.log_info(f"Set value '{value}' to element: {selector}")
            return True, None
        except Exception as e:
            error_message = f"Failed to set value: {str(e)}"
            self.reporting.log_error(error_message)
            return False, error_message

    def get_value(self, selector):
        try:
            value = self.page.input_value(selector)
            self.reporting.log_info(f"Got value '{value}' from element: {selector}")
            return True, value
        except Exception as e:
            error_message = f"Failed to get value: {str(e)}"
            self.reporting.log_error(error_message)
            return False, error_message

    def assert_value(self, selector, expected_value):
        try:
            actual_value = self.page.input_value(selector)
            if str(actual_value) != str(expected_value):
                error_message = f"Assertion failed: Expected '{expected_value}', got '{actual_value}'"
                self.reporting.log_error(error_message)
                return False, error_message
            self.reporting.log_info(f"Assertion passed: {expected_value} == {actual_value}")
            return True, None
        except Exception as e:
            error_message = f"Assertion failed: {str(e)}"
            self.reporting.log_error(error_message)
            return False, error_message

    def element_click(self, selector):
        try:
            self.page.click(selector)
            self.reporting.log_info(f"Clicked element: {selector}")
            return True, None
        except Exception as e:
            error_message = f"Failed to click element {selector}: {str(e)}"
            self.reporting.log_error(error_message)
            return False, error_message

    def scroll_page(self, scroll_count=1):
        try:
            for _ in range(scroll_count):
                self.page.evaluate("window.scrollBy(0, window.innerHeight)")
            self.reporting.log_info(f"Scrolled {scroll_count} time(s) in window")
            return True, None
        except Exception as e:
            error_message = f"Scroll failed: {str(e)}"
            self.reporting.log_error(error_message)
            return False, error_message

    def clear_text(self, selector):
        try:
            self.page.fill(selector, "")
            self.reporting.log_info(f"Cleared text for element: {selector}")
            return True, None
        except Exception as e:
            error_message = f"Failed to clear text: {str(e)}"
            self.reporting.log_error(error_message)
            return False, error_message

    def is_element_visible(self, selector):
        try:
            visible = self.page.is_visible(selector)
            self.reporting.log_info(f"Element visibility for {selector}: {visible}")
            return True, str(visible)
        except Exception as e:
            error_message = f"Failed to check element visibility: {str(e)}"
            self.reporting.log_error(error_message)
            return False, error_message

    def element_exists(self, selector):
        try:
            elements = self.page.query_selector_all(selector)
            exists = len(elements) > 0
            self.reporting.log_info(f"Element exists: {selector}: {exists}")
            return True, exists
        except Exception as e:
            error_message = f"Error in element_exists: {str(e)}"
            self.reporting.log_error(error_message)
            return False, error_message

    def switch_to_tab(self, tab_index):
        try:
            pages = self.context.pages
            if tab_index < 0 or tab_index >= len(pages):
                error_message = f"Tab index {tab_index} out of range. Available tabs: {len(pages)}"
                self.reporting.log_error(error_message)
                return False, error_message
            self.page = pages[tab_index]
            log_message = f"Switched to browser tab: {tab_index}"
            self.reporting.log_info(log_message)
            return True, log_message
        except Exception as e:
            error_message = f"Failed to switch to browser tab: {str(e)}"
            self.reporting.log_error(error_message)
            return False, error_message

    def reload_window(self):
        try:
            self.page.reload()
            log_message = "Reloaded the current browser window successfully."
            self.reporting.log_info(log_message)
            return True, log_message
        except Exception as e:
            error_message = f"Failed to reload the current browser window: {str(e)}"
            self.reporting.log_error(error_message)
            return False, error_message

    def send_downarrow_then_tab(self, selector):
        try:
            self.page.focus(selector)
            self.page.keyboard.press('ArrowDown')
            self.page.keyboard.press('Tab')
            time.sleep(1)
            log_message = "Pressed down arrow and tab key."
            self.reporting.log_info(log_message)
            return True, log_message
        except Exception as e:
            error_message = f"Failed to press down arrow and tab key: {str(e)}"
            self.reporting.log_error(error_message)
            return False, error_message

    def quit(self):
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.reporting.log_info("Browser closed and cleanup completed")
