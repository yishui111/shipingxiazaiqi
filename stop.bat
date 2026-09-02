@echo off
rem ============================================================
rem  Bili Video Downloader - stop server
rem ============================================================
cd /d "%~dp0"

if not exist "data\server.pid" (
    echo Server is not running, no PID file.
    exit /b 0
)

set /p PID=<data\server.pid
taskkill /PID %PID% /F >nul 2>nul
if errorlevel 1 (
    echo Failed to kill process %PID%, it may have already exited.
) else (
    echo Server stopped, PID %PID%.
)
del "data\server.pid" >nul 2>nul
