@echo off
setlocal enabledelayedexpansion

title QuizFlow Launcher
cd /d "%~dp0\.."

echo ===================================================
echo   QuizFlow - Unified Platform Launcher
echo ===================================================
echo.

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found in system PATH.
    pause
    exit /b 1
)

echo [*] Starting FastAPI Backend Server...
start "QuizFlow Backend Server" /min cmd /c "cd /d "%~dp0..\backend" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

timeout /t 2 /nobreak >nul

echo [*] Launching Desktop Application...
cd /d "%~dp0..\desktop"
python main.py
