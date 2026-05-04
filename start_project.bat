@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo    DnD Conquer - One-Click Start
echo ==========================================

echo [1/2] Starting backend server (debug_server.py)...
start "DnD_Debug_Server" cmd /c "python debug_server.py"

echo [2/2] Waiting for server...
timeout /t 3 >nul

echo [3/3] Opening browser...
start http://localhost:8765

echo.
echo Server started! Please operate in the browser.
echo To stop the server, press Ctrl+C in the popped up command window.
echo.
pause
