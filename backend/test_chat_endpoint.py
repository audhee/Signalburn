"""Test /chat endpoint end-to-end."""
import threading, time, requests, sys, os
import io

# Fix Windows console encoding for emoji output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ".")

def start_server():
    import uvicorn
    from app.main import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

print("Starting server...")
t = threading.Thread(target=start_server, daemon=True)
t.start()
print("Waiting 65s for RAG init...")
time.sleep(65)
print("Testing /chat endpoint...\n")

p = 0
f = 0

# Test 1: snake bite (first-aid, should get answer)
try:
    r = requests.post("http://127.0.0.1:8000/api/v1/ai/chat",
                      json={"question": "snake bite on my hand"}, timeout=60)
    d = r.json()
    a = str(d.get("answer", ""))
    print("TEST 1 (snake bite): status=%d" % r.status_code)
    print("  answer: %s" % a[:300])
    if r.status_code == 200 and len(a) > 20:
        print("  -> PASS\n"); p += 1
    else:
        print("  -> FAIL\n"); f += 1
except Exception as e:
    print("  -> FAIL: %s\n" % e); f += 1

# Test 2: cancer (should be BLOCKED)
try:
    r2 = requests.post("http://127.0.0.1:8000/api/v1/ai/chat",
                       json={"question": "I got cancer"}, timeout=30)
    d2 = r2.json()
    a2 = str(d2.get("answer", ""))
    bl = any(w in a2.lower() for w in ["outside","consult","not found","blocked","knowledge base"])
    print("TEST 2 (cancer): status=%d" % r2.status_code)
    print("  answer: %s" % a2[:300])
    if bl:
        print("  -> PASS (BLOCKED)\n"); p += 1
    else:
        print("  -> FAIL (NOT BLOCKED)\n"); f += 1
except Exception as e:
    print("  -> FAIL: %s\n" % e); f += 1

# Test 3: diet plan (should be BLOCKED)
try:
    r3 = requests.post("http://127.0.0.1:8000/api/v1/ai/chat",
                       json={"question": "give me a diet plan for weight loss"}, timeout=30)
    d3 = r3.json()
    a3 = str(d3.get("answer", ""))
    bl3 = any(w in a3.lower() for w in ["outside","consult","not found","blocked","knowledge base"])
    print("TEST 3 (diet plan): status=%d" % r3.status_code)
    print("  answer: %s" % a3[:300])
    if bl3:
        print("  -> PASS (BLOCKED)\n"); p += 1
    else:
        print("  -> FAIL (NOT BLOCKED)\n"); f += 1
except Exception as e:
    print("  -> FAIL: %s\n" % e); f += 1

# Test 4: burn (first-aid, should get answer)
try:
    r4 = requests.post("http://127.0.0.1:8000/api/v1/ai/chat",
                       json={"question": "how to treat a burn"}, timeout=60)
    d4 = r4.json()
    a4 = str(d4.get("answer", ""))
    print("TEST 4 (burn): status=%d" % r4.status_code)
    print("  answer: %s" % a4[:300])
    if r4.status_code == 200 and len(a4) > 20:
        print("  -> PASS\n"); p += 1
    else:
        print("  -> FAIL\n"); f += 1
except Exception as e:
    print("  -> FAIL: %s\n" % e); f += 1

print("=" * 60)
print("RESULTS: %d/%d passed, %d failed" % (p, p + f, f))
if f == 0:
    print("ALL TESTS PASSED!")
else:
    print("SOME TESTS FAILED")
print("=" * 60)
