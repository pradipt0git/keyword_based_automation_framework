import logging
from datetime import datetime
import os
import shutil
import openpyxl
from selenium import webdriver
from tempfile import NamedTemporaryFile
from string import Template

class RobustReporting:
    def __init__(self):
        self.values_dict = {}
        self._init_logging()
        os.makedirs('Reports', exist_ok=True)        

    def _init_logging(self):
        """Initialize enhanced logging system"""
        log_dir = 'Logs'
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(
            log_dir, f"execution_{datetime.now().strftime('%Y%m%d')}.log")

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('robust_reporting')

    # def start_execution_log(self, report_path):
    #     """Start a new execution log."""
    #     execution_log_file = f"execution_{datetime.now().strftime('%Y%m%d')}.log"
    #     execution_log_path = os.path.join(os.path.dirname(report_path), execution_log_file)
    #     execution_handler = logging.FileHandler(execution_log_path)
    #     execution_formatter = logging.Formatter('%(asctime)s - %(message)s')
    #     execution_handler.setFormatter(execution_formatter)
    #     self.logger.addHandler(execution_handler)

    def log_info(self, message):
        """Log informational message"""
        self.logger.info(message)

    def log_error(self, message):
        """Log error message"""
        self.logger.error(message)

    
    # Move generate_html_report to module level (not inside RobustReporting)
    def generate_html_report(self, excel_path, template_path, html_output_path):
        try:
            import pandas as pd
            from datetime import datetime
            import os
            # Read the Excel report
            df = pd.read_excel(excel_path)
            # Count pass/fail
            pass_count = (df['execution_status'].str.lower() == 'pass').sum()
            fail_count = (df['execution_status'].str.lower() == 'fail').sum()
            # Helper to wrap long paths for display
            def wrap_path(path, maxlen=50):
                if not path:
                    return ''
                if len(path) <= maxlen:
                    return path
                # Insert <wbr> at every maxlen interval for HTML wrapping
                return '<wbr>'.join([path[i:i+maxlen] for i in range(0, len(path), maxlen)])

            # Prepare test results rows with wrapped screenshot paths and thumbnail images
            test_results_rows = ''
            for _, row in df.iterrows():
                # Show blank for NaN error message
                error_msg = '' if pd.isna(row['error message']) else row['error message']
                # Show thumbnail image if screenshot exists, else blank
                if pd.notna(row['screenshot']) and row['screenshot']:
                    thumb_html = (
                        f'<a href="{row["screenshot"]}" target="_blank">'
                        f'<img src="{row["screenshot"]}" alt="screenshot" style="max-width:80px;max-height:60px;border:1px solid #888;vertical-align:middle;"/>'
                        f'</a>'
                    )
                else:
                    thumb_html = ''
                test_results_rows += f"<tr class='{row['execution_status'].lower()}'>" \
                    f"<td>{row['testcasename']}</td>" \
                    f"<td>{row.get('dataset number','')}</td>" \
                    f"<td>{row['action']}</td>" \
                    f"<td>{row['execution_status']}</td>" \
                    f"<td>{error_msg}</td>" \
                    f"<td>{thumb_html}</td></tr>"

            # Wrap report_path, log_path, screenshot_path for display in header
            display_report_path = wrap_path(excel_path)
            display_log_path = wrap_path(os.path.join(os.path.dirname(excel_path), 'execution_log.txt'))
            display_screenshot_path = wrap_path(os.path.join(os.path.dirname(excel_path), 'Screenshots'))

            # Read and update template
            with open(template_path, encoding='utf-8') as f:
                template = f.read()
            # Remove teststep, add testset number (dataset number)
            template = template.replace('<th>Test Step</th>', '<th>Test Set Number</th>')
            # Fill template
            now = datetime.now()
            # Move the replacements BEFORE creating the Template object
            template = template.replace('{{execution_date}}', '$execution_date')
            template = template.replace('{{execution_time}}', '$execution_time')
            template = template.replace('{{report_path}}', '$report_path')
            template = template.replace('{{log_path}}', '$log_path')
            template = template.replace('{{screenshot_path}}', '$screenshot_path')
            template = template.replace('{pass_count}', '$pass_count')
            template = template.replace('{fail_count}', '$fail_count')
            template = template.replace('{{test_results_rows}}', '$test_results_rows')
            template = Template(template)
            html = template.safe_substitute(
                execution_date=now.strftime('%Y-%m-%d'),
                execution_time=now.strftime('%H:%M:%S'),
                report_path=display_report_path,
                log_path=display_log_path,
                screenshot_path=display_screenshot_path,
                pass_count=pass_count,
                fail_count=fail_count,
                test_results_rows=test_results_rows
            )
            # Write HTML
            with open(html_output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            # --- Testcase-wise HTML report generation ---
            testcase_reports_dir = os.path.join(os.path.dirname(html_output_path), 'testcase_reports')
            os.makedirs(testcase_reports_dir, exist_ok=True)
            for testcase in df['testcasename'].unique():
                testcase_df = df[df['testcasename'] == testcase]
                testcase_rows = ''
                for _, row in testcase_df.iterrows():
                    error_msg = '' if pd.isna(row['error message']) else row['error message']
                    if pd.notna(row['screenshot']) and row['screenshot']:
                        thumb_html = (
                            f'<a href="{row["screenshot"]}" target="_blank">'
                            f'<img src="{row["screenshot"]}" alt="screenshot" style="max-width:80px;max-height:60px;border:1px solid #888;vertical-align:middle;"/>'
                            f'</a>'
                        )
                    else:
                        thumb_html = ''
                    testcase_rows += f"<tr class='{row['execution_status'].lower()}'>" \
                        f"<td>{row['testcasename']}</td>" \
                        f"<td>{row.get('dataset number','')}</td>" \
                        f"<td>{row['action']}</td>" \
                        f"<td>{row['execution_status']}</td>" \
                        f"<td>{error_msg}</td>" \
                        f"<td>{thumb_html}</td></tr>"
                testcase_html = template.safe_substitute(
                    execution_date=now.strftime('%Y-%m-%d'),
                    execution_time=now.strftime('%H:%M:%S'),
                    report_path=display_report_path,
                    log_path=display_log_path,
                    screenshot_path=display_screenshot_path,
                    pass_count=(testcase_df['execution_status'].str.lower() == 'pass').sum(),
                    fail_count=(testcase_df['execution_status'].str.lower() == 'fail').sum(),
                    test_results_rows=testcase_rows
                )
                testcase_html_path = os.path.join(testcase_reports_dir, f"{testcase}.html")
                with open(testcase_html_path, 'w', encoding='utf-8') as f:
                    f.write(testcase_html)
            # --- End testcase-wise HTML report generation ---
        except Exception as e:
            self.log_error(f"Failed to generate HTML report: {e}")
            print(f"[ERROR] Failed to generate HTML report: {e}")
