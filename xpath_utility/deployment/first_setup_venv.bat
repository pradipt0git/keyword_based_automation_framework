@echo off
REM One-time setup script for portable deployment
cd /d %~dp0
cd ..

REM Create virtual environment
python -m venv .venv

REM Activate and install requirements
call .venv\Scripts\activate
pip install --upgrade pip
pip install -r deployment\requirements.txt

pause
