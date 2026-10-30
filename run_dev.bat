@echo off
title TrustRank - Dev Mode (Frontend + Backend)
echo ========================================================
echo Starting TrustRank in Development Mode
echo ========================================================

echo Starting Backend API Server (Port 8000)...
start "TrustRank Backend" cmd /k "cd /d "%~dp0backend" && .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

ping -n 3 127.0.0.1 >nul

echo Starting Frontend Vite Dev Server (Port 5173)...
start "TrustRank Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

ping -n 4 127.0.0.1 >nul
start "" http://localhost:5173
echo Dev servers started!
