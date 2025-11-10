@echo off
title Activity Tracker Server
cd /d "%~dp0"
echo Starting Activity Tracker...
echo Opening browser in 2 seconds...
start /min cmd /c "timeout /t 2 /nobreak > nul && start http://127.0.0.1:5000"
REM Ensure virtual environment exists
if not exist "venv\Scripts\python.exe" (
	echo Virtual environment not found. Please create it and install requirements.
	echo python -m venv venv
	echo venv\Scripts\python.exe -m pip install -r requirements.txt
	pause
	exit /b 1
)
REM Launch run.py entry point
venv\Scripts\python.exe run.py
echo Server stopped.
pause
