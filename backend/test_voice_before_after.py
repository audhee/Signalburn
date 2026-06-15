"""
test_voice_before_after.py - Compare Voice Assistant Responses
Before Fine-Tuning (Groq cloud) vs After Fine-Tuning (Ollama + sashwat_optimized RAG)

Usage:
  python test_voice_before_after.py
  python test_voice_before_after.py --query "Mere pair mein bahut dard hai"

Environment:
  USE_LOCAL_MODEL=false -> Groq cloud (BEFORE)
  USE_LOCAL_MODEL=true  -> Ollama fine-tuned (AFTER)
"""
import os, sys, json, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

DEFAULT_QUERIES = [
    "Mere pair mein bahut dard hai, kya karu?",
    "Saans lene mein takleef ho rahi hai",
    "Sar mein bahut dard hai aur ulti ho rahi hai",
    "Hath mein kat laga hai aur khoon bah raha hai",
    "Gir gaya hai aur pair toot gaya lagta hai",
]

def query_groq_direct(query, language="hi"):
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        return {"response": "GROQ_API_KEY not set", "success": False, "latency_s": 0}
    from groq import Groq
    from app.services.ai.rag_service import rag_service
    from app.services.ai.prompt_utils import build_system_prompt
    from app.services.ai.language_service import detect_language
    client = Groq(api_key=groq_key)
    lang_info = detect_language(query)
    language_name = lang_info["language_name"]
    is_emergency = lang_info["is_emergency"]
    rag_context = rag_service.retrieve_context(query, k=5, source="sashwat_optimized")
    rag_context = rag_context[:6000] if rag_context else ""
    system_prompt = build_system_prompt(language_name, rag_context, is_emergency)
    try:
        start = time.time()
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
            temperature=0.1, max_tokens=700,
        )
        elapsed = time.time() - start
        return {"response": response.choices[0].message.content.strip(), "language": language_name, "latency_s": round(elapsed, 2), "success": True, "model": "Groq llama-3.1-8b-instant", "rag_source": "sashwat_optimized"}
    except Exception as e:
        return {"response": str(e), "success": False, "latency_s": 0, "model": "Groq"}

def query_ollama_direct(query, language="hi"):
    ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "arohan-medical")
    import requests
    from app.services.ai.rag_service import rag_service
    from app.services.ai.prompt_utils import build_system_prompt
    from app.services.ai.language_service import detect_language
    lang_info = detect_language(query)
    language_name = lang_info["language_name"]
    is_emergency = lang_info["is_emergency"]
    rag_context = rag_service.retrieve_context(query, k=5, source="sashwat_optimized")
    rag_context = rag_context[:6000] if rag_context else ""
    system_prompt = build_system_prompt(language_name, rag_context, is_emergency)
    payload = {"model": ollama_model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": query}], "stream": False, "options": {"temperature": 0.1, "top_p": 0.9, "repeat_penalty": 1.1}}
    try:
        start = time.time()
        resp = requests.post(ollama_url + "/api/chat", json=payload, timeout=120)
        elapsed = time.time() - start
        if resp.status_code == 200:
            result = resp.json()
            return {"response": result["message"]["content"].strip(), "language": language_name, "latency_s": round(elapsed, 2), "success": True, "model": "Ollama " + ollama_model, "rag_source": "sashwat_optimized"}
        return {"response": "HTTP " + str(resp.status_code), "success": False, "latency_s": round(elapsed, 2), "model": "Ollama " + ollama_model}
    except requests.exceptions.ConnectionError:
        return {"response": "Cannot connect to Ollama at " + ollama_url, "success": False, "latency_s": 0, "model": "Ollama " + ollama_model}
    except Exception as e:
        return {"response": str(e), "success": False, "latency_s": 0, "model": "Ollama " + ollama_model}

def run_comparison(queries, language="hi"):
    sep = "=" * 72
    print("\n" + sep)
    print("  DEMO COMPARISON: Before Fine-Tuning vs After Fine-Tuning")
    print(sep + "\n")
    results = []
    for i, query in enumerate(queries, 1):
        print("\n" + "-" * 72)
        print("  Query " + str(i) + ": \"" + query + "\"")
        print("-" * 72)
        print("\n  [BEFORE] Groq cloud (no fine-tuning)...")
        before = query_groq_direct(query, language)
        print("  Model: " + before.get("model", "?"))
        print("  Latency: " + str(before.get("latency_s", "?")) + "s")
        if before["success"]:
            for line in before["response"].split("\n"):
                print("    " + line)
        else:
            print("  ERROR: " + before["response"])
        print("\n  [AFTER] Ollama fine-tuned model...")
        after = query_ollama_direct(query, language)
        print("  Model: " + after.get("model", "?"))
        print("  Latency: " + str(after.get("latency_s", "?")) + "s")
        if after["success"]:
            for line in after["response"].split("\n"):
                print("    " + line)
        else:
            print("  ERROR: " + after["response"])
        results.append({"query": query, "before_groq": before, "after_ollama": after})
    print("\n\n" + sep)
    print("  SUMMARY")
    print(sep + "\n")
    ok_b = len([r for r in results if r["before_groq"]["success"]])
    ok_a = len([r for r in results if r["after_ollama"]["success"]])
    avg_b = sum(r["before_groq"].get("latency_s", 0) for r in results if r["before_groq"]["success"]) / max(ok_b, 1)
    avg_a = sum(r["after_ollama"].get("latency_s", 0) for r in results if r["after_ollama"]["success"]) / max(ok_a, 1)
    print("  Queries: " + str(len(queries)))
    print("  Groq OK: " + str(ok_b) + "/" + str(len(queries)))
    print("  Ollama OK: " + str(ok_a) + "/" + str(len(queries)))
    print("  Avg Groq: " + "{:.2f}".format(avg_b) + "s")
    print("  Avg Ollama: " + "{:.2f}".format(avg_a) + "s")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_before_after_results.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n  Saved: " + out)
    print(sep + "\n")
    return results

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--query", "-q", type=str)
    p.add_argument("--language", "-l", type=str, default="hi")
    args = p.parse_args()
    queries = [args.query] if args.query else DEFAULT_QUERIES
    run_comparison(queries, args.language)

if __name__ == "__main__":
    main()
