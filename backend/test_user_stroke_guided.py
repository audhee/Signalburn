import requests
import json
import sys

def test_user_stroke_guided():
    url = "http://127.0.0.1:8000/api/v1/ai/guided-query"
    
    # EXACT context from the user's mobile app interaction
    context = (
        "Q: What happened?\n"
        "A: i got acute ischemic brain stroke\n"
        "Q: What is the age and gender of the person?\n"
        "A: age is 20 and gender is male\n"
        "Q: Do they have any medical conditions or take regular medication?\n"
        "A: No.\n"
        "Q: Is the bleeding heavy?\n"
        "A: It s bleeding heavily.\n"
        "Q: Has it stopped?\n"
        "A: Noted."
    )
    
    payload = {
        "text": "Noted.",
        "context": context,
        "language": "en",
        "rag_source": "sashwat_optimized"
    }
    
    print("Sending user's guided-query stroke request to backend...")
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            
            with open("test_user_stroke_guided_result.txt", "w", encoding="utf-8") as f:
                f.write("API Response Status: Success\n")
                f.write(f"Language: {result.get('language')}\n")
                f.write(f"RAG Source Used: {result.get('rag_source')}\n")
                f.write("\nResponse Text:\n")
                f.write(response_text)
                
            print("Successfully wrote response to test_user_stroke_guided_result.txt")
        else:
            print(f"Error from API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"API request failed: {e}")

if __name__ == "__main__":
    test_user_stroke_guided()
