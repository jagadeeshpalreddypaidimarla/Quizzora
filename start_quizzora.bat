@echo off
title Quizzora Setup and Launcher
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.12 or newer from https://www.python.org/downloads/
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  py -m venv .venv
  if errorlevel 1 goto error
)
call ".venv\Scripts\activate.bat"
echo Installing required packages...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 goto error
if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo.
  echo IMPORTANT: A .env file was created.
  echo Open .env in Notepad and set ADMIN_PASSWORD and SECRET_KEY before continuing.
  echo Save it, then run start_quizzora.bat again.
  start notepad ".env"
  pause
  exit /b 0
)
echo Starting Quizzora at http://127.0.0.1:8000
echo Keep this window open while using the website.
python -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
exit /b 0
:error
echo Setup failed. Check the error above, then try again.
pause
