import logging
from datetime import datetime
import os
import shutil
import openpyxl
from selenium import webdriver
from tempfile import NamedTemporaryFile

class RobustReporting:
    def __init__(self):
        self.values_dict = {}
        self._init_logging()
        os.makedirs('Reports', exist_ok=True)
        os.makedirs('Backups', exist_ok=True)

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

    def start_execution_log(self, report_path):
        """Start a new execution log."""
        execution_log_file = f"execution_{datetime.now().strftime('%Y%m%d')}.log"
        execution_log_path = os.path.join(os.path.dirname(report_path), execution_log_file)
        execution_handler = logging.FileHandler(execution_log_path)
        execution_formatter = logging.Formatter('%(asctime)s - %(message)s')
        execution_handler.setFormatter(execution_formatter)
        self.logger.addHandler(execution_handler)

    def log_info(self, message):
        """Log informational message"""
        self.logger.info(message)

    def log_error(self, message):
        """Log error message"""
        self.logger.error(message)

    def log_execution(self, action, field_name=None, error_message=None):
        """Log execution details."""
        if field_name:
            self.logger.info(f"{action} for {field_name}")
        else:
            self.logger.info(action)
        if error_message:
            self.logger.error(error_message)

    def _validate_excel_file(self, filepath):
        """Validate Excel file integrity"""
        try:
            # Create temp file with .xlsx extension
            with NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                with open(filepath, 'rb') as src:
                    tmp.write(src.read())
                tmp_path = tmp.name

            try:
                wb = openpyxl.load_workbook(tmp_path)
                wb.close()
                return True
            except Exception as e:
                self.log_error(f"File validation failed: {str(e)}")
                return False
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass  # Ignore cleanup errors

    def _create_backup(self, filepath):
        """Create timestamped backup copy"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(
            'Backups', f"{os.path.basename(filepath)}_backup_{timestamp}.xlsx")
        shutil.copy2(filepath, backup_path)
        return backup_path

    def copy_excel_template(self, template_path: str) -> str:
        """Safely copy Excel template with validation"""
        try:
            if not os.path.exists(template_path):
                raise FileNotFoundError(
                    f"Template not found at {template_path}")

            if not self._validate_excel_file(template_path):
                raise ValueError("Template file is corrupted")

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            execution_folder = os.path.join('Reports', timestamp)
            os.makedirs(execution_folder, exist_ok=True)
            os.makedirs(os.path.join(execution_folder,
                        'Screenshots'), exist_ok=True)

            report_filename = f"report_{timestamp}.xlsx"
            report_path = os.path.join(execution_folder, report_filename)

            # Create backup of template first
            self._create_backup(template_path)

            # Copy using binary mode with verification
            with open(template_path, 'rb') as src, open(report_path, 'wb') as dst:
                data = src.read()
                dst.write(data)
                dst.flush()
                os.fsync(dst.fileno())

            # Verify copy
            if os.path.getsize(report_path) != os.path.getsize(template_path):
                raise IOError("File copy incomplete - size mismatch")

            if not self._validate_excel_file(report_path):
                raise ValueError("Copied file failed validation")

            os.chmod(report_path, 0o777)
            self.log_info(f"Successfully created report at: {report_path}")
            return report_path

        except Exception as e:
            self.log_error(f"Failed to copy template: {str(e)}")
            raise

    def capture_screenshot(self, driver: webdriver.Chrome, report_path: str, step_name: str):
        """Capture screenshot and save to file, return path"""
        try:
            # Screenshots go in Screenshots subfolder of execution folder
            execution_folder = os.path.dirname(report_path)
            screenshot_dir = os.path.join(execution_folder, 'Screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)

            # Generate filename
            timestamp = datetime.now().strftime('%H%M%S')
            filename = f"{step_name}_{timestamp}.png"
            screenshot_path = os.path.join(screenshot_dir, filename)

            # Save screenshot
            driver.save_screenshot(screenshot_path)
            self.log_info(f"Screenshot saved to: {screenshot_path}")
            return screenshot_path

        except Exception as e:
            self.log_error(f"Failed to capture screenshot: {str(e)}")
            return None
