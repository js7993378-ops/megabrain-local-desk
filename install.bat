@echo off
echo ========================================
echo Installing Trading Desk Dependencies
echo ========================================
echo.

cd /d C:\Users\Dell\hermes-trading-desk

echo Step 1: Creating virtual environment...
uv venv

echo Step 2: Installing packages...
uv pip install -r requirements.txt

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Test scanner: .\venv\Scripts\python.exe fomo_local.py
echo   2. Run desk: .\venv\Scripts\python.exe main.py
echo.
pause