# main.py
# This script serves as the main entry point for the automation framework.
# It initializes the reporting system, processes test cases, and generates reports.

# Import necessary modules and libraries
from modules.reporting_v2 import RobustReporting as Reporting
from modules.selenium_actions import SeleniumActions
from datetime import datetime
import os
import openpyxl
from jinja2 import Template  # For HTML templating
import base64
from io import BytesIO
import shutil
import sys
import tempfile

def ensure_config_folder():
    """Ensure the config folder is available in the execution folder."""
    exe_dir = os.path.dirname(os.path.abspath(__file__))
    execution_dir = os.getcwd()
    config_source = os.path.join(exe_dir, 'config')
    config_target = os.path.join(execution_dir, 'config')

    # Check if the config folder already exists in the execution folder
    if not os.path.exists(config_target):
        if os.path.exists(config_source):
            shutil.copytree(config_source, config_target)
        else:
            raise FileNotFoundError("Config folder is missing in the executable.")

    return config_target

# Ensure the config folder is available during execution
config_folder_path = ensure_config_folder()

# Ensure Logs and Reports folders exist
logs_folder = os.path.join(os.getcwd(), 'Logs')
reports_folder = os.path.join(os.getcwd(), 'Reports')
os.makedirs(logs_folder, exist_ok=True)
os.makedirs(reports_folder, exist_ok=True)

# Create a new folder for custom actions
custom_actions_folder = os.path.join(os.path.dirname(__file__), 'custom_actions')
os.makedirs(custom_actions_folder, exist_ok=True)

# Function to generate an HTML report from test results
def generate_html_report(report_path, html_path, test_results, execution_details):
    """Generate an HTML report from test results."""
    # Load the HTML template from the config folder
    template_path = os.path.join(config_folder_path, 'html_template.html')
    with open(template_path, 'r', encoding='utf-8') as template_file:
        html_template = template_file.read()

    # Generate a chart for test summary
    statuses = [result['action_status'] for result in test_results]
    pass_count = statuses.count("PASS")
    fail_count = statuses.count("FAIL")

    # Initialize test_results_rows to store HTML rows for test results
    test_results_rows = ""

    # Update the HTML generation logic to apply background color only for Action Status
    for result in test_results:
        test_results_rows += "<tr>"
        if result['rowspan_test_name']:
            test_results_rows += f"<td rowspan=\"{result['rowspan_test_name']}\">{result['test_name']}</td>"
        if result['rowspan_test_step']:
            test_results_rows += f"<td rowspan=\"{result['rowspan_test_step']}\">{result['test_step']}</td>"
        # Safely retrieve action and field_name
        action = result.get('step_action', 'Unknown Action')
        field_name = result.get('field_name', '')

        # Update Step Action format
        step_action_text = f"{action} for {field_name}" if field_name else f"{action}"
        test_results_rows += f"<td>{step_action_text}</td>"
        test_results_rows += f"<td class=\"{'pass' if result['action_status'] == 'PASS' else 'fail'}\">{result['action_status']}</td>"
        test_results_rows += f"<td>{result['error_message'] or ''}</td>"
        if result['screenshot']:
            test_results_rows += f"<td><a href=\"{result['screenshot']}\" target=\"_blank\"><img src=\"{result['screenshot']}\" alt=\"Screenshot\"></a></td>"
        else:
            test_results_rows += "<td>N/A</td>"
        test_results_rows += "</tr>"

    # Replace placeholders for dynamic data
    html_content = html_template.replace("{{execution_date}}", execution_details['date'])
    html_content = html_content.replace("{{execution_time}}", execution_details['time'])
    html_content = html_content.replace("{pass_count}", str(pass_count))
    html_content = html_content.replace("{fail_count}", str(fail_count))
    html_content = html_content.replace("{{report_path}}", execution_details['report_path'])
    html_content = html_content.replace("{{log_path}}", execution_details['log_path'])
    html_content = html_content.replace("{{screenshot_path}}", execution_details['screenshot_path'])
    html_content = html_content.replace("{{test_results_rows}}", test_results_rows)

    # Write the final HTML content to the file
    with open(html_path, "w", encoding="utf-8") as html_file:
        html_file.write(html_content)

# Function to process test cases from Excel file and generate HTML report
def process_testcases(report_path, reporter):
    """Process test cases from Excel file and generate HTML report."""
    try:
        # Initialize Selenium
        selenium = SeleniumActions(reporter)

        # Load Excel file
        wb = openpyxl.load_workbook(report_path)
        sheet = wb.active

        # Get column indices (assuming first row has headers)
        headers = [cell.value for cell in sheet[1]]
        execute_col = headers.index("Execute") + 1  # 1-based index
        action_col = headers.index("Action") + 1
        value_col = headers.index("Value") + 1
        xpath_col = headers.index("Locator_Xpath") + 1
        test_name_col = headers.index("TestName") + 1
        test_step_col = headers.index("TestStep") + 1

        # Remove 'FieldCode' column from headers if it exists
        if "FieldCode" in headers:
            headers.remove("FieldCode")

        # Ensure 'Action' column is retained in headers
        if "Action" not in headers:
            raise ValueError("'Action' column is missing in the Excel template.")

        # Add 'Action Status', 'Error Message', and 'Screenshot' columns if they don't exist
        if "Action Status" not in headers:
            headers.append("Action Status")
        if "Error Message" not in headers:
            headers.append("Error Message")
        if "Screenshot" not in headers:
            headers.append("Screenshot")

        # Remove 'Test Step Status' and 'Test Case Status' columns from headers if they exist
        headers = [header for header in headers if header not in ["Test Step Status", "Test Case Status"]]

        # Create a new workbook for execution
        execution_wb = openpyxl.Workbook()
        execution_sheet = execution_wb.active

        # Update the sheet with modified headers
        for col_idx, header in enumerate(headers, start=1):
            execution_sheet.cell(row=1, column=col_idx, value=header)

        # Filter out rows where Execute = 'N' and ensure only valid rows are processed
        rows_to_copy = [row for row in sheet.iter_rows(min_row=2) if row[execute_col-1].value == "Y"]

        # Ensure 'Action' column is correctly copied and 'FieldCode' column is excluded
        for row_idx, row in enumerate(rows_to_copy, start=2):
            for col_idx, cell in enumerate(row, start=1):
                header = headers[col_idx - 1]
                if header == "Action":
                    execution_sheet.cell(row=row_idx, column=col_idx, value=row[action_col - 1].value)  # Copy Action column data
                elif header != "FieldCode":  # Skip 'FieldCode' column
                    execution_sheet.cell(row=row_idx, column=col_idx, value=cell.value)

        # Save the execution workbook
        execution_wb.save(report_path)

        # Reload the execution workbook to ensure only valid rows are processed
        wb = openpyxl.load_workbook(report_path)
        sheet = wb.active

        test_results = []  # Collect test results for HTML report

        # Create execution-specific log file
        execution_log_path = os.path.join(os.path.dirname(report_path), "execution.log")
        with open(execution_log_path, "w", encoding="utf-8") as execution_log:
            execution_log.write(f"Execution log for {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Define the column index for 'Screenshot'
        screenshot_col = headers.index("Screenshot") + 1  # 1-based index

        # Define the column indices for 'Action Status' and 'Error Message'
        action_status_col = headers.index("Action Status") + 1  # 1-based index
        error_col = headers.index("Error Message") + 1  # 1-based index

        # Process rows
        for row_idx, row in enumerate(sheet.iter_rows(min_row=2), start=2):  # Skip header
            if row[execute_col-1].value == "Y":  # Check Execute column
                test_name = row[test_name_col-1].value
                test_step = row[test_step_col-1].value
                action = row[action_col-1].value
                xpath = row[xpath_col-1].value
                value = row[value_col-1].value

                # Extract field name from the Excel sheet
                field_name_col = headers.index("FieldName") + 1  # Assuming 'FieldName' is the column header
                field_name = row[field_name_col - 1].value if field_name_col else None

                # Update step action text
                step_action_text = f"{action}" if xpath else action

                reporter.log_info(
                    f"Executing: {action} on {xpath} with value {value}")
                with open(execution_log_path, "a", encoding="utf-8") as execution_log:
                    execution_log.write(f"Executing: {action} on {xpath} with value {value}\n")

                stacktrace = None  # Initialize stacktrace variable
                try:
                    # Dynamically call custom action if action starts with 'custom-'
                    if action.startswith("custom-"):
                        action_name = action.replace("custom-", "")
                        try:
                            # Import the custom_actions module dynamically
                            import importlib
                            custom_actions = importlib.import_module("custom_actions.custom_actions")

                            # Get the function from the custom_actions module
                            custom_function = getattr(custom_actions, action_name, None)

                            if custom_function:
                                # Call the custom function with the required arguments
                                success, message = custom_function(
                                    selenium.driver, xpath, value, field_name, None, test_step, test_name
                                )
                            else:
                                success, message = False, f"Custom function '{action_name}' not found in custom_actions.py"
                        except Exception as e:
                            success, message = False, f"Error calling custom function '{action_name}': {str(e)}"
                    else:
                        # Existing action handling logic
                        if action == "open_url":
                            success, message = selenium.open_url(value)
                        elif action == "set_value":
                            success, message = selenium.set_value(xpath, value)
                        elif action == "get_value":
                            success, message = selenium.get_value(xpath)
                        elif action == "assert_value":
                            success, message = selenium.assert_value(xpath, value)
                        elif action == "element_click":
                            success, message = selenium.element_click(xpath)
                        elif action == "scroll_page":
                            success, message = selenium.scroll_page(int(value) if value else 1)
                        else:
                            success, message = False, "Unknown action"

                    if success:
                        action_status = "PASS"
                        error_message = None
                    else:
                        action_status = "FAIL"
                        error_message = message

                except Exception as e:
                    action_status = "FAIL"
                    error_message = str(e)
                    reporter.log_error(f"Error executing action: {error_message}")
                    stacktrace= str(e)  # Capture stacktrace for developers
                    # Log detailed error messages for failed actions
                    with open(execution_log_path, "a", encoding="utf-8") as execution_log:
                        execution_log.write(f"Error: {error_message}\n")
                        execution_log.write(f"Stacktrace: {stacktrace}\n")  # Include stacktrace for developers
                        execution_log.write(f"Action Status: {action_status}\n")

                # Log detailed information for each action in the execution log
                with open(execution_log_path, "a", encoding="utf-8") as execution_log:
                    execution_log.write(f"Field Name: {field_name}\n")
                    execution_log.write(f"Action: {action}\n")
                    execution_log.write(f"Value: {value}\n")
                    execution_log.write(f"Status: {action_status}\n")
                    if action_status == "FAIL":
                        execution_log.write(f"Error: {error_message}\n")
                        execution_log.write(f"Stacktrace: {stacktrace}\n")  # Include stacktrace for developers
                    execution_log.write("\n")

                # Capture and insert screenshot in dedicated column if failed
                if action_status == "FAIL":
                    screenshot_path = reporter.capture_screenshot(
                        selenium.driver, report_path, f"step_{row_idx}")
                    if screenshot_path:
                        rel_path = os.path.relpath(
                            screenshot_path, os.path.dirname(report_path))
                        sheet.cell(
                            row=row_idx, column=screenshot_col, value=rel_path)
                        reporter.log_info(
                            f"Screenshot path saved to report: {rel_path}")

                # Save action status and error message in Excel
                sheet.cell(row=row_idx, column=action_status_col, value=action_status)
                if action_status == "FAIL":
                    sheet.cell(row=row_idx, column=error_col, value=error_message)

                # Append test result for HTML report
                test_results.append({
                    "test_name": test_name,
                    "test_step": test_step,
                    "step_action": step_action_text,
                    "action_status": action_status,
                    "test_step_status": None,  # Placeholder for later calculation
                    "test_case_status": None,  # Placeholder for later calculation
                    "error_message": error_message if action_status == "FAIL" else None,
                    "screenshot": rel_path if action_status == "FAIL" else None,
                    "rowspan_test_name": None,  # To be calculated later
                    "rowspan_test_step": None,  # To be calculated later
                    "field_name": field_name  # Add field name to test results
                })

        # Calculate Test Step Status and Test Case Status
        for test_result in test_results:
            test_result["test_step_status"] = "PASS" if all(
                r["action_status"] == "PASS" for r in test_results if r["test_step"] == test_result["test_step"]) else "FAIL"
            test_result["test_case_status"] = "PASS" if all(
                r["test_step_status"] == "PASS" for r in test_results if r["test_name"] == test_result["test_name"]) else "FAIL"

        # Calculate rowspan for TestName and TestStep
        for key in ["test_name", "test_step"]:
            rowspan_key = f"rowspan_{key}"
            current_value = None
            rowspan_count = 0
            for idx, result in enumerate(test_results):
                if result[key] == current_value:
                    result[rowspan_key] = None
                    rowspan_count += 1
                else:
                    if rowspan_count > 0:
                        test_results[idx - rowspan_count][rowspan_key] = rowspan_count
                    current_value = result[key]
                    rowspan_count = 1
            if rowspan_count > 0:
                test_results[-rowspan_count][rowspan_key] = rowspan_count

        # Final save
        wb.save(report_path)

        # Generate HTML report
        execution_details = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "report_path": report_path,
            "log_path": execution_log_path,
            "screenshot_path": os.path.join(os.path.dirname(report_path), "Screenshots")
        }
        html_path = report_path.replace(".xlsx", ".html")
        generate_html_report(report_path, html_path,
                             test_results, execution_details)

        # Cleanup
        selenium.quit()
        wb.close()
        return True

    except Exception as e:
        reporter.log_error(f"Error processing testcases: {str(e)}")
        execution_log.write(f"Error processing testcases: {str(e)}" )
        return False


# Main function to initialize reporting and process test cases
def main():
    # Initialize reporting system
    reporter = Reporting()

    try:
        # Copy template to execution folder with timestamp
        template_path = os.path.join(config_folder_path, 'testcase_template.xlsx')
        report_path = reporter.copy_excel_template(template_path)
        reporter.log_info(f"Report created at: {report_path}")
        reporter.log_info(f"Execution folder: {os.path.dirname(report_path)}")

        # Process test cases
        process_testcases(report_path, reporter)
        return report_path

    except Exception as e:
        reporter.log_error(f"Error in report generation: {str(e)}")
        return None


if __name__ == "__main__":
    main()
