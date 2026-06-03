import requests
import json
import sys

def test_guided_query_hindi():
    url = "http://127.0.0.1:8000/api/v1/ai/guided-query"
    
    # Simulate a Hindi guided query flow
    context = (
        "Q: What happened?\n"
        "A: मेरी नाक से धूप की वजह से खून बह रहा है।\n"
        "Q: What is the age and gender of the person?\n"
        "A: पुरुष, उम्र 20 वर्ष।\n"
        "Q: Do they have any medical conditions or take regular medication?\n"
        "A: नहीं।\n"
        "Q: Is the bleeding heavy?\n"
        "A: हाँ, बहुत तेज़ बह रहा है।\n"
        "Q: Has it stopped?\n"
        "A: अभी तक नहीं।"
    )
    
    payload = {
        "text": "अभी तक नहीं।",
        "context": context,
        "language": "hi",
        "rag_source": "sashwat_optimized"
    }
    
    print("Sending final Hindi guided-query request to backend...")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            
            with open("test_guided_query_hindi_result.txt", "w", encoding="utf-8") as f:
                f.write("API Response Status: Success\n")
                f.write(f"Language: {result.get('language')}\n")
                f.write(f"RAG Source Used: {result.get('rag_source')}\n")
                f.write("\nResponse Text:\n")
                f.write(response_text)
                
            print("Successfully wrote response to test_guided_query_hindi_result.txt")
        else:
            print(f"Error from API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"API request failed: {e}")

if __name__ == "__main__":
    test_guided_query_hindi()
