import os
import json
import time
import keyboard
from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import WebDriverException


# Path to EdgeDriver (update if needed)
EDGEDRIVER_PATH = r'C:\\WebDriver\\msedgedriver.exe'  # Update path as needed

# Predefined URL
default_url = 'https://www.google.com'

# JSON output file
selectors_csv = 'element_selectors.csv'
selectors_json = 'element_selectors.json'

def close_all_browsers():
    # Windows: close all Chrome processes
    os.system('taskkill /F /IM chrome.exe >nul 2>&1')
    time.sleep(2)

def open_browser(url):
    options = Options()
    # Edge does not support 'detach' option like Chrome, so we skip it
    driver = webdriver.Edge(service=Service(EDGEDRIVER_PATH), options=options)
    driver.get(url)
    return driver


def get_element_details(driver, element):
    details = {}
    try:
        # Properties
        props = {}
        props['ariaLabel'] = element.get_attribute('aria-label')
        props['className'] = element.get_attribute('class')
        props['href'] = element.get_attribute('href')
        props['id'] = element.get_attribute('id')
        props['name'] = element.get_attribute('name')
        props['role'] = element.get_attribute('role')
        props['tag'] = element.tag_name.upper()
        props['text'] = element.text
        props['title'] = element.get_attribute('title')
        props['type'] = element.get_attribute('type')
        props['value'] = element.get_attribute('value')
        # Get bounding rect
        rect = driver.execute_script('var r=arguments[0].getBoundingClientRect(); return {x:r.x, y:r.y, top:r.top, left:r.left, bottom:r.bottom, right:r.right, width:r.width, height:r.height};', element)
        props['rect'] = rect
        # Center point
        props['x'] = rect['x'] + rect['width']/2 if rect else None
        props['y'] = rect['y'] + rect['height']/2 if rect else None
        details['properties'] = props

        # Selectors
        selectors = {}
        class_name = props['className']
        tag = element.tag_name
        selectors['Class Name'] = class_name
        if class_name:
            first_class = class_name.split()[0]
            selectors['CSS Selector (Class)'] = f'.{first_class}'
            selectors['XPath (Class)'] = f"//*[contains(@class, '{first_class}')]"
            selectors['CSS Selector (Combined)'] = f"{tag}.{'.'.join(class_name.split())}"
            selectors['XPath (Combined)'] = f"//{tag}[contains(@class, '{first_class}')]"
        else:
            selectors['CSS Selector (Class)'] = None
            selectors['XPath (Class)'] = None
            selectors['CSS Selector (Combined)'] = None
            selectors['XPath (Combined)'] = None
        # Add id, name, etc. selectors if present
        if props['id']:
            selectors['CSS Selector (ID)'] = f"#{props['id']}"
            selectors['XPath (ID)'] = f"//*[@id='{props['id']}']"
        if props['name']:
            selectors['CSS Selector (Name)'] = f"{tag}[name='{props['name']}']"
            selectors['XPath (Name)'] = f"//{tag}[@name='{props['name']}']"
        # Add generic
        selectors['Tag'] = tag

        # Add full XPath and most relative XPath using browser's developer tools logic
        # Full XPath (absolute):
        full_xpath = driver.execute_script('''
            function getElementXPath(elt) {
                var path = '';
                for (; elt && elt.nodeType == 1; elt = elt.parentNode) {
                    idx = 1;
                    for (var sib = elt.previousSibling; sib; sib = sib.previousSibling) {
                        if (sib.nodeType == 1 && sib.nodeName == elt.nodeName) idx++;
                    }
                    var xname = elt.nodeName.toLowerCase();
                    path = '/' + xname + '[' + idx + ']' + path;
                }
                return path;
            }
            return getElementXPath(arguments[0]);
        ''', element)
        selectors['Full XPath'] = full_xpath

        # Most relative XPath (copy as relative from devtools):
        # This is usually the shortest unique XPath from the element to the root with id if available
        relative_xpath = driver.execute_script('''
            function getRelativeXPath(elt) {
                if (elt.id !== '') {
                    return '//*[@id="' + elt.id + '"]';
                }
                var path = '';
                for (; elt && elt.nodeType == 1; elt = elt.parentNode) {
                    var sibCount = 0;
                    var sibIndex = 0;
                    for (var sib = elt.parentNode ? elt.parentNode.firstChild : null; sib; sib = sib.nextSibling) {
                        if (sib.nodeType == 1 && sib.nodeName == elt.nodeName) {
                            sibCount++;
                            if (sib === elt) sibIndex = sibCount;
                        }
                    }
                    var xname = elt.nodeName.toLowerCase();
                    var segment = xname + (sibCount > 1 ? '[' + sibIndex + ']' : '');
                    path = '/' + segment + path;
                    if (elt.parentNode && elt.parentNode.nodeType == 1 && elt.parentNode.id) {
                        path = '//*[@id="' + elt.parentNode.id + '"]' + path;
                        break;
                    }
                }
                return path;
            }
            return getRelativeXPath(arguments[0]);
        ''', element)
        selectors['Relative XPath'] = relative_xpath

        # Add smart/shortest unique XPath (like DevTools) as accu_xpath
        accu_xpath = None
        try:
            accu_xpath = driver.execute_script('''
                function getSmartXPath(element) {
                    if (!element) return '';
                    // Prefer id if unique
                    if (element.id && document.querySelectorAll('#' + CSS.escape(element.id)).length === 1) {
                        return '//*[@id="' + element.id + '"]';
                    }
                    // Prefer name if unique
                    if (element.name && document.querySelectorAll('[name="' + CSS.escape(element.name) + '"]').length === 1) {
                        return '//' + element.tagName.toLowerCase() + '[@name="' + element.name + '"]';
                    }
                    // Prefer class if unique
                    if (element.className && typeof element.className === 'string') {
                        var classes = element.className.trim().split(/\s+/);
                        for (var i = 0; i < classes.length; i++) {
                            var cls = classes[i];
                            if (cls && document.querySelectorAll('.' + CSS.escape(cls)).length === 1) {
                                return '//' + element.tagName.toLowerCase() + '[contains(@class, "' + cls + '")]';
                            }
                        }
                    }
                    // Otherwise, build a unique path up the tree
                    var path = [];
                    while (element && element.nodeType === 1 && element !== document.body) {
                        var tag = element.tagName.toLowerCase();
                        var siblings = element.parentNode ? Array.from(element.parentNode.children).filter(function(e) { return e.tagName === element.tagName; }) : [];
                        if (siblings.length > 1) {
                            var idx = siblings.indexOf(element) + 1;
                            path.unshift(tag + '[' + idx + ']');
                        } else {
                            path.unshift(tag);
                        }
                        element = element.parentNode;
                    }
                    return '//' + path.join('/');
                }
                return getSmartXPath(window.clickedElement);
            ''')
        except Exception:
            accu_xpath = None
        selectors['accu_xpath'] = accu_xpath
        details['selectors'] = selectors
    except Exception as e:
        details['error'] = str(e)
    return details

def get_xpath(element):
    # Selenium 4+ has get_dom_attribute, but for compatibility, build xpath manually
    path = ''
    while element is not None:
        parent = element.find_element(By.XPATH, '..') if element.tag_name != 'html' else None
        siblings = []
        if parent:
            siblings = parent.find_elements(By.XPATH, f'./{element.tag_name}')
        idx = siblings.index(element) + 1 if siblings else 1
        path = f'/{element.tag_name}[{idx}]' + path
        element = parent
    return path

def get_css_selector(element):
    selector = element.tag_name
    if element.get_attribute('id'):
        selector += f"#{element.get_attribute('id')}"
    elif element.get_attribute('class'):
        selector += '.' + '.'.join(element.get_attribute('class').split())
    return selector

def enable_capture_js(driver):
    js = '''
    if (!window._captureHandler) {
        window._captureHandler = function(e) {
            e.preventDefault();
            window.clickedElement = e.target;
        };
        document.body.addEventListener('click', window._captureHandler, true);
    }
    '''
    driver.execute_script(js)

def disable_capture_js(driver):
    js = '''
    if (window._captureHandler) {
        document.body.removeEventListener('click', window._captureHandler, true);
        window._captureHandler = null;
    }
    '''
    driver.execute_script(js)

def capture_elements(driver, selectors_list):
    # Check for clicked element and append selectors
    import csv
    clicked = driver.execute_script('return window.clickedElement || null;')
    if clicked:
        elem = driver.execute_script('return window.clickedElement;')
        element = driver.execute_script('return arguments[0];', elem)
        details = get_element_details(driver, driver.switch_to.active_element)
        print('Element details:', details)
        # --- CSV: Only append name, value, type, text (max 40 chars), full_xpath, relative_xpath ---
        name = details['properties'].get('name', '')
        value = details['properties'].get('value', '')
        typ = details['properties'].get('type', '')
        text = details['properties'].get('text', '')
        if text and len(text) > 40:
            text = text[:40]
        full_xpath = details['selectors'].get('Full XPath', '')
        relative_xpath = details['selectors'].get('Relative XPath', '')
        row = [name, value, typ, text, full_xpath, relative_xpath]
        write_header = not os.path.exists(selectors_csv)
        with open(selectors_csv, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(['name', 'value', 'type', 'text', 'full_xpath', 'relative_xpath'])
            writer.writerow(row)
        print(f'Details appended to {selectors_csv}')
        # --- JSON: Save all data, overwrite on each run ---
        selectors_list.append(details)
        with open(selectors_json, 'w', encoding='utf-8') as f:
            json.dump(selectors_list, f, indent=2, ensure_ascii=False)
        # Reset clickedElement so user can click again
        driver.execute_script('window.clickedElement = null;')


def main():
    close_all_browsers()
    driver = open_browser(default_url)
    print('Press F9 to toggle capture mode (on/off). Click elements to capture selectors. Press F9 again to stop. Repeat as needed. Press Ctrl+C in terminal to exit.')
    selectors_list = []
    capture_mode_enabled = False
    from selenium.common.exceptions import NoSuchWindowException
    try:
        print('Hold Windows + F9 to enable capture mode. Release to disable. Press Ctrl+C in terminal to exit.')
        while True:
            try:
                fn_pressed = keyboard.is_pressed('F9')
                if fn_pressed:
                    if not capture_mode_enabled:
                        capture_mode_enabled = True
                        print('Capture mode enabled.')
                        enable_capture_js(driver)
                else:
                    if capture_mode_enabled:
                        capture_mode_enabled = False
                        print('Capture mode disabled.')
                        disable_capture_js(driver)
                if capture_mode_enabled:
                    capture_elements(driver, selectors_list)
                time.sleep(0.1)
            except NoSuchWindowException:
                print('Browser window was closed. Exiting loop.')
                break
    except KeyboardInterrupt:
        print('Exiting...')
    finally:
        try:
            disable_capture_js(driver)
        except Exception:
            pass
        try:
            driver.quit()
        except Exception:
            pass

if __name__ == '__main__':
    main()
