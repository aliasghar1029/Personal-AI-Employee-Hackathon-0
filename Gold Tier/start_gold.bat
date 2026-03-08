@echo off
REM ===========================================
REM Gold Tier AI Employee - One Click Start
REM ===========================================
REM This script starts all Gold Tier services
REM including Facebook, Odoo, and error recovery
REM ===========================================

echo ========================================
echo Starting Gold Tier AI Employee...
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

REM Create necessary directories
if not exist "Logs" mkdir Logs
if not exist "AI_Employee_Vault\Social\Facebook_Queue" mkdir AI_Employee_Vault\Social\Facebook_Queue
if not exist "AI_Employee_Vault\Logs\audit" mkdir AI_Employee_Vault\Logs\audit
if not exist "AI_Employee_Vault\Logs\errors" mkdir AI_Employee_Vault\Logs\errors
if not exist "AI_Employee_Vault\Pending_Approval\ODOO" mkdir AI_Employee_Vault\Pending_Approval\ODOO
if not exist "AI_Employee_Vault\Approved\ODOO" mkdir AI_Employee_Vault\Approved\ODOO
if not exist "facebook_session" mkdir facebook_session

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found
    echo Creating .env from .env.example...
    if exist "AI_Employee_Vault\.env.example" (
        copy "AI_Employee_Vault\.env.example" ".env"
        echo Please edit .env file with your API credentials
        echo.
    ) else if exist ".env.example" (
        copy ".env.example" ".env"
        echo Please edit .env file with your API credentials
        echo.
    )
)

echo Starting Gold Tier services in separate windows...
echo.

REM Start Gmail Watcher (Silver Tier)
echo [1/10] Starting Gmail Watcher...
start "Gmail Watcher" cmd /k "cd /d %~dp0AI_Employee_Vault && python gmail_watcher.py"
timeout /t 2 /nobreak >nul

REM Start WhatsApp Watcher (Silver Tier)
echo [2/10] Starting WhatsApp Watcher...
start "WhatsApp Watcher" cmd /k "cd /d %~dp0AI_Employee_Vault && python whatsapp_watcher.py"
timeout /t 2 /nobreak >nul

REM Start File System Watcher (Silver Tier)
echo [3/10] Starting File System Watcher...
start "File System Watcher" cmd /k "cd /d %~dp0AI_Employee_Vault && python filesystem_watcher.py"
timeout /t 2 /nobreak >nul

REM Start LinkedIn Poster (Silver Tier)
echo [4/10] Starting LinkedIn Poster...
start "LinkedIn Poster" cmd /k "cd /d %~dp0AI_Employee_Vault && python linkedin_poster.py"
timeout /t 2 /nobreak >nul

REM Start Facebook Manager (Gold Tier - NEW)
echo [5/10] Starting Facebook Manager (Gold Tier)...
start "Facebook Manager" cmd /k "cd /d %~dp0AI_Employee_Vault && python facebook_manager.py"
timeout /t 2 /nobreak >nul

REM Start Email MCP Server (Silver Tier)
echo [6/10] Starting Email MCP Server...
start "Email MCP" cmd /k "cd /d %~dp0AI_Employee_Vault && python email_mcp_server.py"
timeout /t 2 /nobreak >nul

REM Start Odoo MCP Server (Gold Tier - NEW)
echo [7/10] Starting Odoo MCP Server (Gold Tier)...
start "Odoo MCP" cmd /k "cd /d %~dp0AI_Employee_Vault && python odoo_mcp_server.py"
timeout /t 2 /nobreak >nul

REM Start Scheduler (Silver Tier)
echo [8/10] Starting Scheduler...
start "Scheduler" cmd /k "cd /d %~dp0AI_Employee_Vault && python scheduler.py"
timeout /t 2 /nobreak >nul

REM Start CEO Briefing Generator (Gold Tier - NEW)
echo [9/10] Starting CEO Briefing Generator (Gold Tier)...
start "CEO Briefing" cmd /k "cd /d %~dp0AI_Employee_Vault && python ceo_briefing.py"
timeout /t 2 /nobreak >nul

REM Start Error Recovery System (Gold Tier - NEW)
echo [10/10] Starting Error Recovery System (Gold Tier)...
start "Error Recovery" cmd /k "cd /d %~dp0AI_Employee_Vault && python error_recovery.py"
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo All Gold Tier services started successfully!
echo ========================================
echo.
echo Running services:
echo   BRONZE TIER:
echo     - File System Watcher
echo   SILVER TIER:
echo     - Gmail Watcher (checks every 2 minutes)
echo     - WhatsApp Watcher (checks every 60 seconds)
echo     - LinkedIn Poster (checks every 60 seconds)
echo     - Email MCP Server (processes approved emails)
echo     - Scheduler (orchestrates all tasks)
echo   GOLD TIER:
echo     - Facebook Manager (API + Playwright fallback)
echo     - Odoo MCP Server (accounting integration)
echo     - CEO Briefing Generator (weekly reports)
echo     - Error Recovery System (health monitoring)
echo.
echo Additional services you can start manually:
echo   - Audit Logger: python audit_logger.py
echo   - Docker Odoo: docker-compose up -d
echo.
echo Check AI_Employee_Vault/Dashboard.md in Obsidian
echo to monitor your AI Employee's activity.
echo.
echo Press Ctrl+C in each window to stop individual watchers
echo Close all windows to stop the AI Employee
echo.
echo ========================================
echo Gold Tier Features:
echo   - Facebook Integration (API + Playwright)
echo   - Odoo Accounting via Docker
echo   - Weekly CEO Briefings
echo   - Error Recovery & Health Monitoring
echo   - Comprehensive Audit Logging
echo ========================================
echo.
pause
