<#
.SYNOPSIS
Switch between Ollama and Groq models for Arohan
.DESCRIPTION
This PowerShell script helps you switch between the fine-tuned Ollama model and the Groq API.
.PARAMETER Mode
Specifies the mode: "ollama" for local model, "groq" for cloud API
.EXAMPLE
.\switch_model_mode.ps1 -mode ollama
Switches to Ollama mode
.EXAMPLE
.\switch_model_mode.ps1 -mode groq
Switches to Groq mode
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("ollama", "groq")]
    [string]$mode
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Arohan Model Mode Switcher" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if ($mode -eq "ollama") {
    Write-Host "Switching to Fine-tuned Ollama model..." -ForegroundColor Yellow
    "USE_LOCAL_MODEL=true" | Out-File -FilePath ".env" -Encoding UTF8
    "OLLAMA_URL=http://localhost:11434" | Out-File -FilePath ".env" -Encoding UTF8 -Append
    "OLLAMA_MODEL=arohan-medical" | Out-File -FilePath ".env" -Encoding UTF8 -Append
    "GROQ_API_KEY=" | Out-File -FilePath ".env" -Encoding UTF8 -Append
    
    Write-Host "" -ForegroundColor Green
    Write-Host "✅ Switched to Ollama mode" -ForegroundColor Green
    Write-Host ""
    Write-Host "Make sure:" -ForegroundColor Yellow
    Write-Host "1. Ollama is running: ollama serve" -ForegroundColor White
    Write-Host "2. Your model is loaded: ollama run arohan-medical" -ForegroundColor White
    Write-Host "3. Restart the backend server" -ForegroundColor White
    Write-Host ""
    Write-Host "To test: curl -X POST `"http://localhost:8000/api/test`" -H `"Content-Type: application/json`" -d `'{"text":"What should I do for a nosebleed?"}'`" -ForegroundColor White
} else {
    Write-Host "Switching to Groq API..." -ForegroundColor Yellow
    "USE_LOCAL_MODEL=false" | Out-File -FilePath ".env" -Encoding UTF8
    "GROQ_API_KEY=" | Out-File -FilePath ".env" -Encoding UTF8 -Append
    
    Write-Host "" -ForegroundColor Green
    Write-Host "✅ Switched to Groq mode" -ForegroundColor Green
    Write-Host ""
    Write-Host "Make sure:" -ForegroundColor Yellow
    Write-Host "1. Your GROQ_API_KEY is set in .env" -ForegroundColor White
    Write-Host "2. Restart the backend server" -ForegroundColor White
    Write-Host ""
    Write-Host "To test: curl -X POST `"http://localhost:8000/api/test`" -H `"Content-Type: application/json`" -d `'{"text":"What should I do for a nosebleed?"}'`" -ForegroundColor White
}

Write-Host "============================================" -ForegroundColor Cyan