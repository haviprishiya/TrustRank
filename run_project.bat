@echo off
title TrustRank - AI Product Recommendation Platform
echo ========================================================
echo Starting TrustRank Platform (Backend + Frontend)
echo ========================================================

cd /d "%~dp0backend"
echo [1/2] Checking Python Virtual Environment...
if not exist ".venv\Scripts\python.exe" (
    echo Error: Python virtual environment not found in backend/.venv
    pause
    exit /b 1
)

echo [2/2] Launching TrustRank Server on http://127.0.0.1:8000 ...
start "" http://127.0.0.1:8000
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
