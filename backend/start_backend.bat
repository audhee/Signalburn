@echo off
echo Starting Arohan Enterprise Backend Development Server...
echo =========================================================
echo Binding to 0.0.0.0 (Accessible to Expo, Ngrok, and LAN devices)
echo Built By Dheeraj A U 

:: Change to the directory where this script sits
cd /d "%~dp0"

:: Activate the virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment natively not found in \venv\Scripts\activate.bat!
    pause
    exit /b 1
)

:: Run Uvicorn explicitly bound
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
