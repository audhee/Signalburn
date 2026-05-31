@echo off
setlocal

cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" "evals\run_eval.py" %*
) else (
    echo [ERROR] Backend virtual environment not found at backend\venv
    exit /b 1
)
