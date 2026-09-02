@echo off
rem ============================================================
rem  Bili Video Downloader - environment check (troubleshooting)
rem ============================================================
chcp 65001 >nul
cd /d "%~dp0"

echo === 1. Python env ===
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" --version
) else (
    echo [MISSING] .venv not found, run install.bat
)

echo.
echo === 2. Key dependencies ===
".venv\Scripts\python.exe" -c "import flask, yt_dlp, imageio_ffmpeg; print('flask', flask.__version__); print('yt-dlp', yt_dlp.version.__version__); print('ffmpeg ->', imageio_ffmpeg.get_ffmpeg_exe())" 2>&1

echo.
echo === 3. Server status ===
if exist "data\server.pid" (
    set /p PID=<data\server.pid
    tasklist /FI "PID eq %PID%" 2>nul | findstr /i "%PID%" >nul && (echo Server running, PID %PID%) || (echo PID file exists but process gone)
) else (
    echo Server not running
)

echo.
echo === 4. Port 8787 ===
netstat -ano | findstr ":8787" | findstr "LISTENING" || echo Port 8787 free

echo.
echo === 5. Folders ===
for %%D in (data downloads logs) do (
    if exist "%%D" (echo OK: %%D) else (echo [MISSING] %%D)
)
echo.
pause
