@echo off
cls
echo ========================================
echo  MEGABRAIN DESK - SCAN TEST
echo ========================================
echo.
echo Testing token scanner...
echo.

cd /d C:\Users\Dell\hermes-trading-desk

uv run python fomo_local.py

echo.
echo ========================================
echo Test Complete!
echo ========================================
pause