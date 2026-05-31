@echo off
echo ============================================
echo   Arohan Model Mode Switcher
echo ============================================
echo.
echo This script will help you switch between:
echo 1. Fine-tuned Ollama model (local)
echo 2. Groq API (cloud)
echo.
set /p choice="Choose mode (1 for Ollama, 2 for Groq): "

if "%choice%"=="1" (
    echo Switching to Fine-tuned Ollama model...
    echo USE_LOCAL_MODEL=true > .env
    echo OLLAMA_URL=http://localhost:11434 >> .env
    echo OLLAMA_MODEL=arohan-medical >> .env
    echo GROQ_API_KEY= >> .env
    echo.
    echo ✅ Switched to Ollama mode
    echo.
    echo Make sure:
    echo 1. Ollama is running: ollama serve
    echo 2. Your model is loaded: ollama run arohan-medical
    echo 3. Restart the backend server
    echo.
    echo To test: curl -X POST "http://localhost:8000/api/ai/test" -H "Content-Type: application/json" -d '{"text":"What should I do for a nosebleed?"}'
) else if "%choice%"=="2" (
    echo Switching to Groq API...
    echo USE_LOCAL_MODEL=false > .env
    echo.
    echo ✅ Switched to Groq mode
    echo.
    echo Make sure:
    echo 1. Your GROQ_API_KEY is set in .env
    echo 2. Restart the backend server
    echo.
    echo To test: curl -X POST "http://localhost:8000/api/ai/test" -H "Content-Type: application/json" -d '{"text":"What should I do for a nosebleed?"}'
) else (
    echo Invalid choice. Please run again and choose 1 or 2.
)

echo.
pause