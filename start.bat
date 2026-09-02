@echo off
rem ============================================================
rem  Bili Video Downloader - start server (opens browser)
rem ============================================================
cd /d "%~dp0"
setlocal enabledelayedexpansion

if not exist ".venv\Scripts\pythonw.exe" (
    echo Dependencies missing. Run install.bat first.
    pause
    exit /b 1
)

if exist "data\server.pid" (
    set /p OLD=<data\server.pid
    tasklist /FI "PID eq !OLD!" 2>nul | findstr /i "!OLD!" >nul
    if not errorlevel 1 (
        echo Downloader is already running, PID !OLD!.
        start "" "http://127.0.0.1:8787"
        exit /b 0
    )
    del "data\server.pid" >nul 2>nul
)

echo Starting Bili Video Downloader ...
powershell -NoProfile -Command "Start-Process -FilePath '%CD%\.venv\Scripts\pythonw.exe' -ArgumentList '-m','app.server' -WorkingDirectory '%CD%'"
echo Started. Browser will open http://127.0.0.1:8787
echo If not opened, visit http://127.0.0.1:8787 manually.
echo Log file: logs\server.log    Stop with: stop.bat
