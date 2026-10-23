@echo off
echo ========================================
echo MEGABRAIN TRADING DESK - TEST SCAN
echo ========================================
echo.

cd /d C:\Users\Dell\hermes-trading-desk

uv run python fomo_local.py

echo.
echo ========================================
echo Test Complete!
echo ========================================
pause