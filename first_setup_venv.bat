@echo off
REM This script creates a Python virtual environment and installs requirements
REM Usage: Double-click or run from command line in the project root

REM Set venv directory name
set VENV_DIR=.venv

REM Check if venv already exists
if exist %VENV_DIR% (
    echo Virtual environment already exists at %VENV_DIR%.
) else (
    echo Creating virtual environment in %VENV_DIR%...
    python -m venv %VENV_DIR%
)

REM Activate the virtual environment
call %VENV_DIR%\Scripts\activate.bat

REM Upgrade pip
REM python -m pip install --upgrade pip

REM Install requirements
if exist requirements.txt (
    echo Installing requirements from requirements.txt...
    pip install -r requirements.txt
) else (
    echo requirements.txt not found. Skipping package installation.
)

echo Virtual environment is ready and activated.
echo To activate it again later, run:
echo     %VENV_DIR%\Scripts\activate.bat
