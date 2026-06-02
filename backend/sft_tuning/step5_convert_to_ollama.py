"""
step5_convert_to_ollama.py - Convert the SFT-trained model to Ollama format.
Creates the Modelfile and provides instructions for Ollama deployment.

Usage:
    python step5_convert_to_ollama.py

This script generates the Ollama Modelfile and conversion instructions.
The actual GGUF file is created in step4 (Colab training script).
"""

import os
import sys

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.join(SCRIPT_DIR, "ollama_deploy")
MODELFILE   = os.path.join(OUTPUT_DIR, "Modelfile")


# ── Arohan System Prompt (matches llm_service.py) ────────────────────────────
AROHAN_SYSTEM_PROMPT = """You are Arohan, a medical first aid assistant for elderly Indians.

RULES:
- Provide clear, numbered first aid steps (6-8 steps)
- Use simple words elderly people understand
- Never diagnose conditions
- Never recommend prescription medications
- Always suggest consulting a doctor for serious conditions
- For emergencies, always end with: Call 112 or 108 immediately
- Respond in the same language the user speaks
- Supported languages: English, Hindi, Kannada, Hinglish, Kanglish"""


def create_modelfile(gguf_path: str = "./arohan-medical-sft.gguf"):
    """Generate an Ollama Modelfile for the SFT model."""
    modelfile_content = f"""# Arohan Medical SFT Model - Ollama Modelfile
# Built from Llama 3 8B Instruct fine-tuned on Sashwat's medical RAG database

FROM {gguf_path}

# Model parameters optimized for medical first aid responses
PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_predict 512
PARAMETER repeat_penalty 1.1
PARAMETER stop "<|eot_id|>"
PARAMETER stop "<|end_of_text|>"

# System prompt
SYSTEM \"\"\"{AROHAN_SYSTEM_PROMPT}\"\"\"

# Chat template (Llama 3 format)
TEMPLATE \"\"\"{{{{ if .System }}}}<|start_header_id|>system<|end_header_id|>

{{{{ .System }}}}<|eot_id|>{{{{ end }}}}{{{{ if .Prompt }}}}<|start_header_id|>user<|end_header_id|>

{{{{ .Prompt }}}}<|eot_id|>{{{{ end }}}}<|start_header_id|>assistant<|end_header_id|>

{{{{ .Response }}}}<|eot_id|>\"\"\"
"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(MODELFILE, "w", encoding="utf-8") as f:
        f.write(modelfile_content)

    return modelfile_content


def create_deployment_script():
    """Create a batch script for Windows deployment."""
    bat_content = """@echo off
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
"""
    bat_file = os.path.join(OUTPUT_DIR, "setup_ollama.bat")
    with open(bat_file, "w") as f:
        f.write(bat_content)

    return bat_file


def create_integration_guide():
    """Create a guide for integrating the SFT model into Arohan."""
    guide = """# Integrating the SFT Model into Arohan

## Option A: Replace Groq with Local Ollama (Full Local)

In `backend/app/services/ai/llm_service.py`, change the model call:

```python
# BEFORE (Groq cloud):
response = groq_client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[...],
)

# AFTER (Local Ollama with SFT model):
import requests

response = requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "arohan-medical",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        "stream": False,
        "options": {"temperature": 0.1}
    }
)
result = response.json()
response_text = result["message"]["content"]
```

## Option B: Keep Groq but Use SFT Knowledge (Hybrid)

Use the SFT-trained model's knowledge to improve the system prompt
in Groq calls. The SFT training teaches the model the response format
and medical knowledge — use this to craft better prompts.

## Option C: Dual Mode (Recommended)

Add a flag in the API to switch between Groq (cloud) and Ollama (local):

```python
# In llm_service.py
USE_LOCAL_MODEL = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"

if USE_LOCAL_MODEL:
    # Use Ollama with arohan-medical model
    response_text = call_ollama(text, system_prompt)
else:
    # Use Groq (existing code)
    response_text = call_groq(text, system_prompt)
```
"""
    guide_file = os.path.join(OUTPUT_DIR, "INTEGRATION_GUIDE.md")
    with open(guide_file, "w", encoding="utf-8") as f:
        f.write(guide)

    return guide_file


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Step 5: Ollama Conversion & Deployment Setup")
    print("=" * 60 + "\n")

    modelfile_content = create_modelfile()
    bat_file = create_deployment_script()
    guide_file = create_integration_guide()

    print(f"[OK] Generated files in: {OUTPUT_DIR}/")
    print("   - Modelfile              - Ollama model configuration")
    print("   - setup_ollama.bat       - Windows deployment script")
    print("   - INTEGRATION_GUIDE.md   - How to plug into Arohan")

    print("\nDeployment Steps:")
    print("   1. Download arohan-medical-sft.gguf from Google Drive")
    print(f"   2. Place it in: {OUTPUT_DIR}/")
    print("   3. Run: setup_ollama.bat")
    print("   4. Test: ollama run arohan-medical")

    print(f"\n   Modelfile preview:")
    for line in modelfile_content.split("\n")[:10]:
        print(f"   {line}")
    print(f"   ...")
