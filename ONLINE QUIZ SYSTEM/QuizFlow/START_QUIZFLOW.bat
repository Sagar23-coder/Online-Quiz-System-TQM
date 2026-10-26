@echo off
setlocal enabledelayedexpansion

title QuizFlow Platform Launcher
cd /d "%~dp0"

echo ===================================================
echo             QUIZFLOW ASSESSMENT PLATFORM
echo ===================================================
echo.
echo [*] Initializing QuizFlow...
echo.

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found in your system PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Start backend server in background window
echo [*] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "QuizFlow Backend Server" /min cmd /c "cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

:: Brief 2-second pause for server startup
timeout /t 2 /nobreak >nul

:: Launch Desktop Client
echo [*] Launching QuizFlow Desktop UI...
cd /d "%~dp0desktop"
python main.py

exit /b 0
