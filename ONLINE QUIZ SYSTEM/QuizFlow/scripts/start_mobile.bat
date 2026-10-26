@echo off
setlocal enabledelayedexpansion

echo ================================================================
echo   QuizFlow - React Native / Expo Mobile Client Launcher
echo ================================================================
echo.

cd /d "%~dp0\..\mobile"

where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

where npx >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] npx command not found.
    pause
    exit /b 1
)

echo Select how you want to launch the Mobile App:
echo.
echo   [1] Open Mobile View in Web Browser (Recommended for PC)
echo       - Opens instantly at http://localhost:8081
echo       - Perfect for viewing mobile UI on Windows without a phone
echo.
echo   [2] Expo Metro QR Mode (For Physical Phone with Expo Go)
echo       - Shows QR code to scan with Expo Go app on iOS/Android
echo.
echo   [3] Expo Tunnel Mode (For Phones on Different Wi-Fi Networks)
echo.
set /p CHOICE="Enter choice [1, 2, or 3] (Press Enter for 1): "

if "%CHOICE%"=="" set CHOICE=1

if "%CHOICE%"=="1" (
    echo.
    echo [*] Starting Mobile Web Preview at http://localhost:8081...
    echo [*] Opening default web browser...
    start http://localhost:8081
    npx expo start --web
) else if "%CHOICE%"=="2" (
    echo.
    echo [*] Starting Expo Metro Bundler for Expo Go / Emulator...
    npx expo start
) else if "%CHOICE%"=="3" (
    echo.
    echo [*] Starting Expo in Tunnel mode...
    npx expo start --tunnel
) else (
    echo Invalid choice. Starting default web mobile view...
    start http://localhost:8081
    npx expo start --web
)

pause
