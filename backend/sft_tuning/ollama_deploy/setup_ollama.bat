@echo off
echo ============================================
echo   Arohan Medical SFT Model - Ollama Setup
echo ============================================
echo.

REM Check if Ollama is installed
where ollama >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Ollama is not installed!
    echo Download from: https://ollama.com/download
    pause
    exit /b 1
)

REM Check if GGUF file exists
if not exist "arohan-medical-sft.gguf" (
    echo ERROR: arohan-medical-sft.gguf not found!
    echo Download it from Google Drive and place it in this folder.
    pause
    exit /b 1
)

echo Creating Ollama model from Modelfile...
ollama create arohan-medical -f Modelfile

echo.
echo ============================================
echo   Model created successfully!
echo ============================================
echo.
echo To test: ollama run arohan-medical
echo To use in Arohan: Update CHROMA_DIR in rag_terminal.py
echo.
pause
