# ========================================
# MEGABRAIN LOCAL TRADING DESK
# ========================================
# Zero cost - No API keys required!
# ========================================

echo Installing dependencies...
uv pip install -r requirements.txt

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To run the desk:
echo   python main.py
echo.
echo To test scanner only:
echo   python fomo_local.py
echo.
pause