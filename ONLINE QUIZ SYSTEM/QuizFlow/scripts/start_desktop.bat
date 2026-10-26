@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   QuizFlow - Starting CustomTkinter Desktop Client
echo ===================================================
echo.

cd /d "%~dp0\..\desktop"

if not exist "main.py" (
    echo [ERROR] Could not find desktop main.py in %cd%
    pause
    exit /b 1
)

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo [*] Launching desktop application...
echo [*] Ensure the backend server is running in another window!
echo.

python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [NOTE] Desktop application exited with code %ERRORLEVEL%.
    pause
)

