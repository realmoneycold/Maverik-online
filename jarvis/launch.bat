@echo off
cd /d C:\Users\mon1ycold\Documents\Maverik\jarvis

:: Start the Python backend silently
start /b python -X utf8 server.py

:: Start the Electron frontend
cd frontend
set NODE_ENV=development
npx electron .
