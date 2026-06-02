# Integrating the SFT Model into Arohan

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
