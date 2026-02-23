@echo off
echo ========================================
echo Starting Silver Tier AI Employee...
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.13 or higher
    pause
    exit /b 1
)

echo Python detected successfully
echo.

REM Create Logs directory if it doesn't exist
if not exist "Logs" mkdir Logs

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found
    echo Creating .env from .env.example...
    if exist ".env.example" (
        copy ".env.example" ".env"
        echo Please edit .env file with your API credentials
        echo.
    )
)

echo Starting watchers in separate windows...
echo.

REM Start Gmail Watcher
echo [1/4] Starting Gmail Watcher...
start "Gmail Watcher" python gmail_watcher.py
timeout /t 2 /nobreak >nul

REM Start WhatsApp Watcher
echo [2/4] Starting WhatsApp Watcher...
start "WhatsApp Watcher" python whatsapp_watcher.py
timeout /t 2 /nobreak >nul

REM Start File System Watcher
echo [3/4] Starting File System Watcher...
start "File System Watcher" python filesystem_watcher.py
timeout /t 2 /nobreak >nul

REM Start Scheduler
echo [4/4] Starting Scheduler...
start "Scheduler" python scheduler.py
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo All watchers started successfully!
echo ========================================
echo.
echo Running services:
echo   - Gmail Watcher (checks every 2 minutes)
echo   - WhatsApp Watcher (checks every 60 seconds)
echo   - File System Watcher (monitors Drop_Here folder)
echo   - Scheduler (orchestrates all tasks)
echo.
echo Additional services you can start manually:
echo   - LinkedIn Poster: python linkedin_poster.py
echo   - Email MCP Server: python email_mcp_server.py
echo.
echo Check AI_Employee_Vault/Dashboard.md in Obsidian
echo to monitor your AI Employee's activity.
echo.
echo Press Ctrl+C in each window to stop individual watchers
echo Close all windows to stop the AI Employee
echo.
echo ========================================
pause
