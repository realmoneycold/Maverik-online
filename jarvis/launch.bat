@echo off
cd /d C:\Users\mon1ycold\Documents\Maverik\jarvis

:: Check if the server is already running on port 8340
netstat -ano | findstr :8340 >nul
if %ERRORLEVEL% equ 0 (
    echo Backend already running.
) else (
    start "" pythonw -X utf8 server.py
)

:: Start the Electron frontend in production mode (uses dist folder instead of Vite dev server)
cd frontend
set NODE_ENV=production
start "" "node_modules\electron\dist\electron.exe" .
