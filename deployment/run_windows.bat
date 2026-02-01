@echo off
REM EstradaBot - Windows Production Launcher
REM
REM This script starts the production server on Windows.
REM For running as a Windows Service, consider using NSSM (Non-Sucking Service Manager).
REM
REM Usage:
REM   1. Copy .env.example to .env and configure
REM   2. Run this script: run_windows.bat

cd /d "%~dp0.."

echo ============================================================
echo EstradaBot - Starting Production Server
echo ============================================================

REM Check if .env exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and configure it.
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found.
    echo Run: python -m venv venv
    echo Then: venv\Scripts\pip install -r requirements.txt
)

REM Set production environment
set FLASK_ENV=production
set FLASK_DEBUG=false

REM Start the server
echo Starting server...
python run_production.py

pause
