import requests
import io
import os

# 1. Configuration
BACKEND_URL = "http://localhost:8000/api/v1/ai/process"
SESSION_ID = "test-session-001"
OUTPUT_FILE = "response_audio.mp3"

print("--- Arohan AI Voice Agent Test ---")
print(f"Target URL: {BACKEND_URL}")
print(f"Session ID using LangGraph Memory: {SESSION_ID}")

# 2. Check for a sample mp3, if none exists, we create a tiny dummy file to simulate the payload.
sample_audio_path = "sample_audio.mp3"
file_to_send = None

if os.path.exists(sample_audio_path):
    print(f"Found local file '{sample_audio_path}'! Will send this to the agent.")
    file_to_send = open(sample_audio_path, "rb")
else:
    print(f"No '{sample_audio_path}' found in current directory.")
    print("Creating an empty dummy 'sample_data.mp3' stream just to test the connectivity/pipeline...")
    # This won't actually transcribe to anything since it's empty, but the agent will still process it.
    # To truly test it, place a real 'sample_audio.mp3' in the backend folder.
    file_to_send = io.BytesIO(b"dummy audio data")

# 3. Form Data Construction
files = {
    "audio": ("test_audio.mp3", file_to_send, "audio/mpeg")
}
data = {
    "session_id": SESSION_ID
}

# 4. Fire Request
print("\nSending request to backend... (Wait a bit, this does STT -> RAG -> LLM -> TTS)")
try:
    response = requests.post(BACKEND_URL, files=files, data=data)
    
    if response.status_code == 200:
        print(f"\n✅ SUCCESS! Received {len(response.content)} bytes of audio data.")
        
        # Check what the pipeline fell back to if audio failed
        if response.headers.get("content-type") == "application/json":
            print("Notice: The backend returned JSON instead of an MP3. Ensure your API keys (Whisper/OpenAI/Sarvam) are in the .env. The LLM text was:")
            print(response.json())
        else:
            with open(OUTPUT_FILE, "wb") as f:
                f.write(response.content)
            print(f"🎉 Saved the returned AI Indian Voice as '{OUTPUT_FILE}' in the current folder!")
            print(f"Conversation tracker header attached: {response.headers.get('X-Conversation-Session')}")
    else:
        print(f"❌ FAILED! Status Code: {response.status_code}")
        print("Details:", response.text)
        
except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: Could not connect to the backend.")
    print("Please make sure your FastAPI backend is running! Open a terminal in the backend folder and run:")
    print("    .\\venv\\Scripts\\Activate.ps1")
    print("    uvicorn app.main:app --reload")

finally:
    if hasattr(file_to_send, "close") and file_to_send is not io.BytesIO:
        file_to_send.close()
