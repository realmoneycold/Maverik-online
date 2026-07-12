#!/bin/bash
# Autostart script for MAVERIK Assistant and Dashboard

# Go to the project directory
cd "/home/ahror/Documents/TPLS AI/MAVERIK-Update/MAVERIK_UPDATE_"

# Export necessary environment variables for audio and display
export DISPLAY=:0
export XAUTHORITY=$HOME/.Xauthority

echo "Starting MAVERIK Control Center Dashboard..."
# Kill any existing uvicorn running on port 8000
lsof -t -i:8000 | xargs -r kill -9 || true
# Start the dashboard in the background
./.venv/bin/python -m uvicorn maverik.dashboard.app:app --host 127.0.0.1 --port 8000 --log-level warning &

echo "Starting MAVERIK Core Voice Agent..."
# Start the main AI process in the foreground
# Using exec so the python process replaces the shell, making signals pass directly to it
exec ./.venv/bin/python main.py
