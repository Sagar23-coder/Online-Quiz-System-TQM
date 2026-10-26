@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   QuizFlow - Seeding Demo Quizzes & Questions
echo ===================================================
echo.

cd /d "%~dp0\..\backend"

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo [*] Seeding demo quiz and questions into quizflow.db...
echo.
python -m app.cli seed-demo

echo.
pause

