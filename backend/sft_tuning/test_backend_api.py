import requests
import json
import sys

def test_api(prompt: str):
    url = "http://127.0.0.1:8000/api/v1/ai/text-query"
    payload = {
        "text": prompt,
        "context": "",
        "language": "en",
        "rag_source": "all"
    }
    
    print(f"Sending text-query API request to backend: '{prompt}'...")
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            print("\nAPI Response:")
            print("=" * 60)
            print(f"Success: {result.get('success')}")
            print(f"Language: {result.get('language')}")
            print(f"Input Type: {result.get('input_type')}")
            print("\nResponse Text:")
            print(result.get('response'))
            print("=" * 60)
        else:
            print(f"Error from API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"API request failed: {e}")

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        query = "What should I do for a nosebleed?"
    test_api(query)
