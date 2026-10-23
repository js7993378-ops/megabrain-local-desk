@echo off
echo ========================================
echo MEGABRAIN TRADING DESK - RUN
echo ========================================
echo.

cd /d C:\Users\Dell\hermes-trading-desk

echo Running desk (shadow mode - safe)...
echo.

uv run python main.py

echo.
echo ========================================
echo Done!
echo ========================================
pause