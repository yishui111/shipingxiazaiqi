@echo off
rem ============================================================
rem  Bili Video Downloader - install dependencies (run once per machine)
rem  Requires: Python 3.10+ ("Add python.exe to PATH" or py launcher)
rem ============================================================
cd /d "%~dp0"

set "PYCMD="
where py >nul 2>nul && set "PYCMD=py -3"
if not defined PYCMD (
    where python >nul 2>nul && set "PYCMD=python"
)
if not defined PYCMD (
    echo [ERROR] Python not found.
    echo Install Python 3.10+ from https://www.python.org/downloads/
    echo and check "Add python.exe to PATH" during installation, then rerun.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/2] Creating virtual environment .venv ...
    %PYCMD% -m venv .venv
    if errorlevel 1 ( echo venv creation failed & pause & exit /b 1 )
) else (
    echo [1/2] Virtual environment exists, skip.
)

echo [2/2] Installing dependencies (versions locked in requirements.txt) ...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 ( echo install failed, check your network & pause & exit /b 1 )

echo.
echo ============================================
echo  Done! Now run start.bat to start the server.
echo ============================================
pause
