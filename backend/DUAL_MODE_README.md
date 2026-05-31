# Arohan Dual Mode Integration

This document explains how to use the dual mode feature that allows switching between the fine-tuned Ollama model and the Groq API.

## Overview

The dual mode system provides two options for generating AI responses:

1. **Local Mode**: Uses the fine-tuned Llama 3 model via Ollama (your SFT-trained model)
2. **Cloud Mode**: Uses the Groq API with the standard Llama 3.3 model

Both modes share the same:
- **System prompt** (`app/services/ai/prompt_utils.py` — `build_system_prompt()`)
- **RAG pipeline** (`app/services/ai/rag_service.py` — optimized FAISS index)
- **Language detection** (`app/services/ai/language_service.py`)
- **Script validation & fallbacks** (`app/services/ai/prompt_utils.py`)

## Configuration

### Environment Variables

Create a `.env` file in the **project root** (or `backend/.env`) with:

```env
# Model Selection
USE_LOCAL_MODEL=false  # Set to "true" for Ollama, "false" for Groq

# Ollama Configuration (only used when USE_LOCAL_MODEL=true)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=arohan-medical

# Groq Configuration (only used when USE_LOCAL_MODEL=false)
GROQ_API_KEY=your_groq_api_key_here
```

### Quick Mode Switching

Use the provided batch script to easily switch between modes:

```bash
cd backend && switch_model_mode.bat
```

This interactive script will help you switch between:
1. Fine-tuned Ollama model (local)
2. Groq API (cloud)

## Setting Up Each Mode

### Mode 1: Fine-tuned Ollama Model (Recommended for Demo)

1. **Start Ollama**:
   ```bash
   ollama serve
   ```

2. **Create your fine-tuned model** (one-time setup):
   ```bash
   ollama create arohan-medical -f sft_tuning/ollama_deploy/Modelfile
   ```
   Or use the setup script:
   ```bash
   cd backend/sft_tuning/ollama_deploy && setup_ollama.bat
   ```

3. **Switch to local mode**:
   ```bash
   echo USE_LOCAL_MODEL=true > .env
   ```

4. **Restart the backend server**:
   ```bash
   cd backend && start_backend.bat
   ```

5. **Test**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/ai/text-query" \
     -H "Content-Type: application/json" \
     -d '{"text":"What should I do for a nosebleed?"}'
   ```

### Mode 2: Groq API (Cloud)

1. **Switch to cloud mode**:
   ```bash
   echo USE_LOCAL_MODEL=false > .env
   ```

2. **Ensure GROQ_API_KEY is set** in `.env`

3. **Restart the backend server**

4. **Test**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/ai/text-query" \
     -H "Content-Type: application/json" \
     -d '{"text":"What should I do for a nosebleed?"}'
   ```

## Testing the Integration

### Health Check

```bash
curl "http://localhost:8000/health"
```

### Multi-Language Testing

```bash
# English
curl -X POST "http://localhost:8000/api/v1/ai/text-query" \
  -H "Content-Type: application/json" \
  -d '{"text":"What should I do if someone faints?"}'

# Hindi
curl -X POST "http://localhost:8000/api/v1/ai/text-query" \
  -H "Content-Type: application/json" \
  -d '{"text":"मेरा नाक से खून आ रहा है","language":"hi"}'

# Kannada
curl -X POST "http://localhost:8000/api/v1/ai/text-query" \
  -H "Content-Type: application/json" \
  -d '{"text":"ನನ್ನ ಕೈ ನೋಯುತ್ತಿದೆ","language":"kn"}'
```

## Demo Preparation

For your demo, I recommend preparing both modes:

1. **Start with Groq mode** (quick setup, guaranteed to work)
2. **Switch to Ollama mode** to showcase your fine-tuned model
3. **Compare responses** between both models to show improvements

### Demo Flow

1. **Introduction**: Explain the dual mode system
2. **Groq Demo**: Show standard responses
3. **Ollama Demo**: Show fine-tuned responses
4. **Comparison**: Highlight improvements in your fine-tuned model

## Troubleshooting

### Ollama Not Available

If you get "Ollama not available" errors:

1. Ensure Ollama is running: `ollama serve`
2. Check loaded models: `ollama list`
3. Verify the model name matches `OLLAMA_MODEL` in `.env`

### Groq API Issues

If you get Groq API errors:

1. Verify your API key is correct in `.env`
2. Check internet connectivity
3. Check the server logs: `backend/server_log.txt`

### Language Detection Issues

If responses are in the wrong language:

1. The system should automatically detect the language
2. Force language by specifying it in the request: `"language":"hi"`
3. Check `app/services/ai/language_service.py` logs

## Files

| File | Purpose |
|------|---------|
| `app/services/ai/prompt_utils.py` | Shared system prompts, script validation, fallback responses |
| `app/services/ai/llm_service.py` | Groq API integration (USE_LOCAL_MODEL=false) |
| `app/services/ai/ollama_service.py` | Local Ollama integration (USE_LOCAL_MODEL=true) |
| `app/services/ai/rag_service.py` | RAG retrieval (optimized FAISS + legacy stores) |
| `app/core/config.py` | Centralized settings from `.env` |
| `sft_tuning/ollama_deploy/` | Fine-tuned GGUF model + Modelfile |
| `switch_model_mode.bat` | Interactive mode-switching script |

## Performance Comparison

| Aspect | Groq API (Cloud) | Fine-tuned Ollama (Local) |
|--------|------------------|---------------------------|
| Response Time | ~1-2 seconds | ~2-4 seconds (depends on hardware) |
| Cost | Free tier available | Free (one-time setup) |
| Privacy | Data sent to cloud | Fully local |
| Customization | Prompt engineering only | Fine-tuned for medical domain |
| Reliability | Depends on internet | Works offline |
