# automation_interface.py
# Defines a common interface for automation actions (Selenium/Playwright)

from abc import ABC, abstractmethod

class AutomationActionsInterface(ABC):
    @abstractmethod
    def open_url(self, url):
        pass

    @abstractmethod
    def set_value(self, selector, value):
        pass

    @abstractmethod
    def get_value(self, selector):
        pass

    @abstractmethod
    def assert_value(self, selector, expected_value):
        pass

    @abstractmethod
    def element_click(self, selector):
        pass

    @abstractmethod
    def scroll_page(self, scroll_count=1):
        pass

    @abstractmethod
    def clear_text(self, selector):
        pass

    @abstractmethod
    def is_element_visible(self, selector):
        pass

    @abstractmethod
    def element_exists(self, selector):
        pass

    @abstractmethod
    def quit(self):
        pass
