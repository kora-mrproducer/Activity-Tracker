@echo off
setlocal
set ACTIVITY_TRACKER_AUTO_TERMINATE=1

cd /d "%~dp0"

set EXE_PATH=dist\ActivityTracker\ActivityTracker.exe
if not exist "%EXE_PATH%" (
  echo Desktop build not found at %EXE_PATH%.
  echo Please build the desktop app first.
  echo Example (PowerShell):
  echo   pyinstaller --noconfirm --onedir --name ActivityTracker --icon static\icons\app.ico desktop_app.py
  pause
  exit /b 1
)

echo Launching Activity Tracker (auto-terminate previous instance enabled)...
"%EXE_PATH%"

endlocal
