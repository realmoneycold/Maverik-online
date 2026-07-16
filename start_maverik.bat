@echo off
echo Starting MAVERIK Control Center Dashboard...

:: Kill any existing uvicorn running on port 8000
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

:: Start the dashboard in the background
start /b .\.venv\Scripts\python.exe -m uvicorn maverik.dashboard.app:app --host 127.0.0.1 --port 8000 --log-level warning

echo Starting MAVERIK Core Voice Agent...

:: Kill any existing Voice Agent processes to prevent overlapping voices
:: Only kills Python processes running main.py (if possible)
wmic process where "name='python.exe' and commandline like '%%main.py%%'" call terminate >nul 2>&1

:: Start the main AI process in the foreground
.\.venv\Scripts\python.exe main.py
