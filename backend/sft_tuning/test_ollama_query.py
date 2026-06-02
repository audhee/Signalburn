import requests
import json
import sys

def test_query(prompt: str):
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "arohan-medical",
        "messages": [
            {
                "role": "system",
                "content": "You are Arohan, a medical first aid assistant for elderly Indians. "
                           "Provide clear, numbered first aid steps using simple words. "
                           "Never diagnose conditions. Never recommend prescription medications. "
                           "Always suggest consulting a doctor for serious or worsening conditions. "
                           "For emergencies, always end with: Call 112 or 108 immediately."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9
        }
    }
    
    print(f"Sending query to local fine-tuned model (arohan-medical): '{prompt}'...")
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            content = result["message"]["content"]
            print("\nResponse:")
            print("=" * 60)
            print(content)
            print("=" * 60)
        else:
            print(f"Error from Ollama: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        query = "What should I do for a nosebleed?"
    test_query(query)
