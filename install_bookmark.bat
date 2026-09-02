@echo off
rem ============================================================
rem  Bili Video Downloader - one-click install bookmark
rem  Close Chrome/Edge first, then run this script.
rem ============================================================
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\install_bookmark.ps1"
pause
