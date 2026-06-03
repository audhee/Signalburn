import requests
import json
import sys

def test_stroke_query():
    url = "http://127.0.0.1:8000/api/v1/ai/text-query"
    payload = {
        "text": "What is acute isomeric brain stroke?",
        "context": "",
        "language": "en",
        "rag_source": "sashwat_optimized"
    }
    
    print("Sending stroke query request to backend...")
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            
            with open("test_stroke_query_result.txt", "w", encoding="utf-8") as f:
                f.write("API Response Status: Success\n")
                f.write(f"Language: {result.get('language')}\n")
                f.write(f"RAG Source Used: {result.get('rag_source', 'sashwat_optimized')}\n")
                f.write("\nResponse Text:\n")
                f.write(response_text)
                
            print("Successfully wrote response to test_stroke_query_result.txt")
        else:
            print(f"Error from API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"API request failed: {e}")

if __name__ == "__main__":
    test_stroke_query()
