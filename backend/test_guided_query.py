import requests
import json
import sys

def test_guided_query():
    url = "http://127.0.0.1:8000/api/v1/ai/guided-query"
    
    # We simulate a completed 5-question context
    context = (
        "Q: What happened?\n"
        "A: My nose is bleeding due to sunlight exposure.\n"
        "Q: What is the age and gender of the person?\n"
        "A: Gender is male and age is 20.\n"
        "Q: Do they have any medical conditions or take regular medication?\n"
        "A: No.\n"
        "Q: Is the bleeding heavy?\n"
        "A: It's bleeding heavily.\n"
        "Q: Has it stopped?\n"
        "A: Not yet."
    )
    
    payload = {
        "text": "Not yet.",
        "context": context,
        "language": "en",
        "rag_source": "sashwat_optimized"
    }
    
    print("Sending final guided-query request to backend...")
    print(f"RAG Source: {payload['rag_source']}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            print("\nAPI Response:")
            print("=" * 60)
            print(f"Success: {result.get('success')}")
            print(f"Mode: {result.get('mode')}")
            print(f"Language: {result.get('language')}")
            print(f"RAG Source Used: {result.get('rag_source')}")
            print("\nResponse Text:")
            print(result.get('response'))
            print("=" * 60)
        else:
            print(f"Error from API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"API request failed: {e}")

if __name__ == "__main__":
    test_guided_query()
