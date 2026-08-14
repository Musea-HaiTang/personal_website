@echo off
setlocal
cd /d %~dp0

echo [1/3] Creating Python virtual environment...
python -m venv backend\.venv
if errorlevel 1 goto :fail

echo [2/3] Installing backend dependencies...
call backend\.venv\Scripts\pip.exe install -r backend\requirements.txt
if errorlevel 1 goto :fail

echo [3/3] Installing frontend dependencies...
cd /d %~dp0frontend
call npm.cmd install
if errorlevel 1 goto :fail

echo.
echo Setup complete. Run start.bat to launch.
pause
exit /b 0

:fail
echo.
echo Setup failed. Please check the error above.
pause
exit /b 1
