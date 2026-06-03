@echo off
echo Starting Arohan Enterprise Backend Development Server...
echo =========================================================
echo Binding to 0.0.0.0 (Accessible to Expo, Ngrok, and LAN devices)
echo Built By Dheeraj A U

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found!
    pause
    exit /b 1
)

python -m uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000