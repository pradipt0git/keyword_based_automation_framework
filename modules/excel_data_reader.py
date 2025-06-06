# excel_data_reader.py
# Module to read execution details and test data from the Excel file in config folder

import os
import openpyxl
import pandas as pd
import re
from modules.automation_process import process_step
from modules.reporting_v2 import RobustReporting
from modules.selenium_actions import SeleniumActions
import datetime
import shutil
import sys

step_results = []
CONFIG_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
EXCEL_FILE = os.path.join(CONFIG_FOLDER, 'testcase_driver_data_sheet.xlsx')

def parse_datasheet_refs(ref_str):
    """
    Parses a string like 'DataSheet!B4:DataSheet!B6' and returns (sheet_name, [row_numbers]).
    Supports single cell or range. Returns (sheet_name, [row_numbers]).
    """
    if not ref_str:
        return None, []
    # Example: DataSheet!B4:DataSheet!B6
    refs = ref_str.split(":")
    row_nums = []
    sheet_name = None
    for ref in refs:
        m = re.match(r"([\w\s]+)!([A-Z]+)(\d+)", ref)
        if m:
            sheet_name = m.group(1)
            row_nums.append(int(m.group(3)))
    if len(row_nums) == 2:
        # Range, fill in-between
        row_nums = list(range(row_nums[0], row_nums[1]+1))
    return sheet_name, row_nums

def get_testcase_to_datarefs_dict(sheet_name='DriverSheet'):
    """
    Returns a dict: {TestCaseName: [(sheet_name, [row_numbers]), ...], ...}
    Only includes testcases where the first occurrence of TestCaseName has Execute == 'Y'.
    Skips blank TestDataSheetReference.
    """
    wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
    if sheet_name not in wb.sheetnames:
        raise ValueError(f"Sheet '{sheet_name}' not found in Excel file.")
    driver_sheet = wb[sheet_name]
    headers = [cell.value for cell in next(driver_sheet.iter_rows(min_row=1, max_row=1))]
    col_idx = {h: i for i, h in enumerate(headers)}
    if 'TestCaseName' not in col_idx or 'TestDataSheetReference' not in col_idx or 'Execute' not in col_idx:
        raise ValueError("Required columns not found in DriverSheet.")
    testcase_first_execute = {}
    testcase_datarefs = {}
    for row in driver_sheet.iter_rows(min_row=2, values_only=True):
        testcase = str(row[col_idx['TestCaseName']]).strip() if row[col_idx['TestCaseName']] else ''
        dataref = str(row[col_idx['TestDataSheetReference']]).strip() if row[col_idx['TestDataSheetReference']] else ''
        execute = str(row[col_idx['Execute']]).strip().upper() if row[col_idx['Execute']] else ''
        if not testcase or not dataref:
            continue
        # Only process testcases where the first occurrence has Execute == 'Y'
        if testcase not in testcase_first_execute:
            testcase_first_execute[testcase] = execute
            if execute != 'Y':
                continue  # Skip this testcase entirely if first occurrence is not Y
        if testcase_first_execute[testcase] != 'Y':
            continue  # Skip all subsequent rows for this testcase if first was not Y
        if testcase not in testcase_datarefs:
            testcase_datarefs[testcase] = []
        sheet, rows = parse_datasheet_refs(dataref)
        if sheet and rows:
            testcase_datarefs[testcase].append((sheet, rows))
    filtered = {tc: refs for tc, refs in testcase_datarefs.items() if testcase_first_execute.get(tc) == 'Y'}
    wb.close()
    return filtered

def process_testcase_rows(testcase, sheet, row_num, driver, reporting, actions, dataset_number):
    try:
        print(f"Processing rows for TestCase: {testcase}")
        # Open Excel and get sheets
        wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
        driver_sheet = wb['DriverSheet']
        common_sheet = wb['CommonSheet']
        data_sheet = wb[sheet]
        # Check if the Execute column in the data_sheet for the given row_num is 'Y'
        header_row = [cell.value for cell in data_sheet[1]]
        execute_col_idx = None
        for idx, col_name in enumerate(header_row):
            if str(col_name).strip().lower() == 'execute':
                execute_col_idx = idx + 1  # 1-based index for openpyxl
                break
        if execute_col_idx:
            execute_value = data_sheet.cell(row=row_num, column=execute_col_idx).value
            if str(execute_value).strip().upper() != 'Y':
                msg = f"Skipping TestCase '{testcase}' DataSheet '{sheet}' Row {row_num}: Execute column is not 'Y'"
                reporting.log_info(msg)
                wb.close()
                return
        # Build CommonSheet lookup: {(Screen, Field): Xpath}
        common_lookup = {}
        for row in common_sheet.iter_rows(min_row=2, values_only=True):
            screen, field, xpath = row[:3]
            if screen and field and xpath:
                common_lookup[(str(screen).strip(), str(field).strip())] = str(xpath).strip()
        # Find column indices in DriverSheet
        headers = [cell.value for cell in next(driver_sheet.iter_rows(min_row=1, max_row=1))]
        col_idx = {h: i for i, h in enumerate(headers)}
        # Loop through DriverSheet rows for this testcase and Execute=Y
        #steps = []
        for row in driver_sheet.iter_rows(min_row=2, values_only=True):
            tc = str(row[col_idx['TestCaseName']]).strip() if row[col_idx['TestCaseName']] else ''
            execute = str(row[col_idx['Execute']]).strip().upper() if row[col_idx['Execute']] else ''
            if tc != testcase or execute != 'Y':
                continue
            screen = str(row[col_idx['Screen']]).strip() if row[col_idx['Screen']] else ''
            field = str(row[col_idx['Field']]).strip() if row[col_idx['Field']] else ''
            action = str(row[col_idx['Action']]).strip() if row[col_idx['Action']] else ''
            xpath = common_lookup.get((screen, field), '')
            data_value = None
            
            # Fetch the header row from data_sheet
            header_row = [cell.value for cell in data_sheet[1]]
            data_value = None
            if field in header_row:
                col_idx_val = header_row.index(field)
                data_value = data_sheet.cell(row=row_num, column=col_idx_val + 1).value  # +1 for 1-based index
            else:
                data_value = ''
            # Now data_value contains the value from the DataSheet for this field
            # Process the step using the automation process function
            step_result = process_step(testcase, screen, field, action, xpath, data_value, driver, reporting, actions,dataset_number)
            #step_result['dataset_number'] = dataset_number
            step_results.append(step_result)
        # Close the workbook after processing    
        wb.close()
    except Exception as e:
        reporting.log_error(f"Error in process_testcase_rows for testcase '{testcase}': {e}")

def initiatedriver(browser='chrome'):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service as ChromeService
        from selenium.webdriver.edge.service import Service as EdgeService
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.edge.options import Options as EdgeOptions
        driver = None
        if browser == 'chrome':
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Suppress logging
            driver = webdriver.Chrome(service=ChromeService(), options=chrome_options)
        elif browser == 'edge':
            edge_options = EdgeOptions()
            edge_options.add_argument('--start-maximized')
            edge_options.add_argument('--no-sandbox')
            edge_options.add_argument('--disable-gpu')
            edge_options.add_argument('--disable-dev-shm-usage')
            edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Suppress logging
            driver = webdriver.Edge(service=EdgeService(), options=edge_options)
        else:
            raise ValueError('Unsupported browser')
        return driver
    except Exception as e:
        RobustReporting().log_error(f"Error in initiatedriver: {e}")
        raise

# Example usage (for testing):
if __name__ == "__main__":                    
    try:
        # Create timestamped report folder
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        report_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Reports', f'execution_report_{timestamp}')
        os.makedirs(report_folder, exist_ok=True)    
        step_results = []
        # Set environment variable for screenshot saving
        os.environ['CURRENT_REPORT_FOLDER'] = report_folder

        print("\nTestCase to DataSheet row mapping:")
        testcase_datarefs = get_testcase_to_datarefs_dict()
        reporting = RobustReporting()       
        for testcase, refs in testcase_datarefs.items():
            dataset_counter = 1
            for sheet, row_nums in refs:
                print(f"  TestCase: {testcase}, DataSheet: {sheet}, Rows: {row_nums}")
                for row_num in row_nums:
                    print(f"    Row {row_num}")
                    browser = 'chrome'  # or 'edge'
                    try:
                        driver = initiatedriver(browser)
                        actions = SeleniumActions(reporting, driver)
                        print(f"TestCase: {testcase}")
                        process_testcase_rows(testcase, sheet, row_num, driver, reporting, actions, dataset_counter)
                        driver.quit()
                    except Exception as e:
                        reporting.log_error(f"Driver or step error for testcase '{testcase}', row {row_num}: {e}")
                    dataset_counter += 1
        # Write report to Excel
        report_df = pd.DataFrame(step_results)
        
        report_path = os.path.join(report_folder, f'execution_report_{timestamp}.xlsx')
        report_df.to_excel(report_path, index=False)
        print(f"Execution report saved to: {report_path}")

        # Generate HTML report
        html_template_path = os.path.join(CONFIG_FOLDER, 'html_template.html')
        html_report_path = os.path.join(report_folder, f'execution_report_{timestamp}.html')
        reporting.generate_html_report(report_path, html_template_path, html_report_path)
        print(f"Execution HTML report saved to: {html_report_path}")
    except Exception as e:
        RobustReporting().log_error(f"Fatal error in __main__: {e}")
    finally:
        if 'CURRENT_REPORT_FOLDER' in os.environ:
            del os.environ['CURRENT_REPORT_FOLDER']
