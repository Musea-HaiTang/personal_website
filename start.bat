@echo off
setlocal
cd /d %~dp0

if not exist "backend\.venv\Scripts\python.exe" (
    echo [ERROR] Missing backend\.venv. Please run setup.bat first.
    pause
    exit /b 1
)
if not exist "frontend\node_modules" (
    echo [ERROR] Missing frontend\node_modules. Please run setup.bat first.
    pause
    exit /b 1
)

start "personal-website-backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
start "personal-website-frontend" cmd /k "cd /d %~dp0frontend && npm.cmd run dev"

timeout /t 3 /nobreak >nul
start "" http://localhost:5173
echo One-click start done: frontend http://localhost:5173 , backend http://127.0.0.1:8000/api/health
