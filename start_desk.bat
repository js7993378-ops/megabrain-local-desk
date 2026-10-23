@echo off
cls
echo ========================================
echo  MEGABRAIN TRADING DESK - STARTED
echo ========================================
echo.
echo Scanning crypto tokens...
echo.

cd /d C:\Users\Dell\hermes-trading-desk

uv run python main.py

echo.
echo ========================================
echo Process finished
echo ========================================
pause