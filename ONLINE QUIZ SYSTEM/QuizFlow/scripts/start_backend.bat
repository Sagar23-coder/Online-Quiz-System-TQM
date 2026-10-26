@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   QuizFlow - Starting FastAPI Backend Server
echo ===================================================
echo.

cd /d "%~dp0\..\backend"

if not exist "app\main.py" (
    echo [ERROR] Could not find app\main.py in %cd%
    pause
    exit /b 1
)

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo [*] Server will listen on http://0.0.0.0:8000
echo [*] Interactive API Docs: http://localhost:8000/docs
echo [*] Health Check URL:    http://localhost:8000/health
echo.
echo Press Ctrl+C in this terminal to stop the server.
echo ===================================================
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause

