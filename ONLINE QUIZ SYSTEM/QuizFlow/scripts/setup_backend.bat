@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   QuizFlow - Backend Environment Setup
echo ===================================================
echo.

:: Locate project root relative to scripts folder
cd /d "%~dp0\.."

:: Check Python availability
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found in your system PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PY_VER=%%i
echo [*] Detected Python version: %PY_VER%
echo [*] Installing backend dependencies from backend\requirements.txt...
echo.

python -m pip install -r backend\requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to install one or more backend dependencies.
    echo Please review the errors above.
    pause
    exit /b 1
)

echo.
echo [*] Initializing database...
cd backend
python -c "from app.database.init_db import init_db; init_db()"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Database initialization failed.
    pause
    exit /b 1
)

echo.
echo ===================================================
echo   Setup Completed Successfully!
echo   Create an administrator account with:
echo     cd backend
echo     python -m app.cli create-admin
echo   You can now run:
echo     - scripts\start_backend.bat
echo     - scripts\start_desktop.bat
echo     - scripts\seed_demo.bat
echo ===================================================
echo.
pause
