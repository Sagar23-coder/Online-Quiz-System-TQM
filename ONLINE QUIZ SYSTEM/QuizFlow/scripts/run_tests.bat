@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   QuizFlow - Running Automated Test Suite
echo ===================================================
echo.

cd /d "%~dp0\..\backend"

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo [*] Running Pytest test suite with isolated database...
echo.
pytest -v
set TEST_STATUS=%ERRORLEVEL%

echo.
echo [*] Running Ruff code linter...
echo.
ruff check app tests
set LINT_STATUS=%ERRORLEVEL%

echo.
echo ===================================================
if %TEST_STATUS% EQU 0 (
    if %LINT_STATUS% EQU 0 (
        echo [SUCCESS] All backend tests and lint checks PASSED!
    ) else (
        echo [WARNING] Tests passed, but linter found issues.
    )
) else (
    echo [FAILURE] Test suite encountered failures.
)
echo ===================================================
echo.
pause
exit /b %TEST_STATUS%

