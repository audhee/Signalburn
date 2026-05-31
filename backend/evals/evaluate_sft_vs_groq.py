"""
evaluate_sft_vs_groq.py
Compares SFT model (Ollama: arohan-medical) vs Groq production (llama-3.3-70b-versatile)
on curated test queries to surface training data quality issues.
"""

import json
import sys
import time
import requests
import re
from pathlib import Path

# --- Configuration -----------------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "arohan-medical"

GROQ_API_KEY = None
try:
    import os
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
except:
    pass

# --- Test Queries ------------------------------------------------------------

TEST_CASES = [
    # -- Bad SFT dataset examples --
    {
        "id": "sft-bad-1",
        "category": "SFT Dataset (Bad)",
        "query": "What will I learn about cardiogenic shock from this chapter?",
        "issue": "Textbook 'refer to chapter' framing -- not a real first aid query",
        "expected_quality": "low -- should say 'Call 112' not 'chapter teaches you'"
    },
    {
        "id": "sft-bad-2",
        "category": "SFT Dataset (Bad)",
        "query": "What is the page number for the section on dressings and bandages?",
        "issue": "Factoid page-number query -- useless for an AI assistant",
        "expected_quality": "low -- AI should not pretend a page number is useful"
    },
    {
        "id": "sft-bad-3",
        "category": "SFT Dataset (Bad)",
        "query": "Are there any precautions I can take to stay safe at home?",
        "issue": "Answer in dataset: 'see section 30.1' -- useless response",
        "expected_quality": "low -- should give actual precautions, not table of contents"
    },
    {
        "id": "sft-bad-4",
        "category": "SFT Dataset (Bad)",
        "query": "What is the role of paramedics in hospitals in Pakistan?",
        "issue": "Irrelevant to Indian users -- wrong geography/context",
        "expected_quality": "low -- should not reference Pakistan paramedics"
    },
    {
        "id": "sft-bad-5",
        "category": "SFT Dataset (Bad)",
        "query": "How can I help prevent asphyxia?",
        "issue": "Dataset answer: 'ways exist but not specified' -- useless",
        "expected_quality": "low -- should give actual prevention tips"
    },
    # -- Real-world first aid queries --
    {
        "id": "real-1",
        "category": "Real-world First Aid",
        "query": "My father has a small bleeding cut on hand. What first aid should I do?",
        "issue": "Standard real-world query the app handles daily",
        "expected_quality": "high -- numbered steps, simple language"
    },
    {
        "id": "real-2",
        "category": "Real-world First Aid",
        "query": "Person is unconscious and not breathing. What should I do right now?",
        "issue": "Emergency -- must say 'Call 112' and give CPR steps",
        "expected_quality": "high -- emergency protocol, 112 mentioned"
    },
    {
        "id": "real-3",
        "category": "Real-world First Aid",
        "query": "My mother has chest pain and is not breathing properly",
        "issue": "Emergency cardiac symptom",
        "expected_quality": "high -- emergency escalation, simple steps"
    },
    {
        "id": "real-4",
        "category": "Real-world First Aid",
        "query": "My father fell in the bathroom and his arm is bleeding.",
        "issue": "Fall + bleeding -- common elderly scenario",
        "expected_quality": "high -- don't move, control bleeding, call for help"
    },
    {
        "id": "real-5",
        "category": "Real-world First Aid (Hindi)",
        "query": "My father fell in the bathroom and his arm is bleeding.",
        "issue": "Hindi query -- must respond in Devanagari",
        "expected_quality": "high -- Hindi script, first aid steps"
    },
    {
        "id": "real-6",
        "category": "Real-world First Aid",
        "query": "My child has a burn from boiling water. What should I do?",
        "issue": "Common household burn scenario",
        "expected_quality": "high -- cool burn, cover, don't apply ice directly"
    },
    {
        "id": "real-7",
        "category": "Real-world First Aid (Hinglish)",
        "query": "mera bhai behosh hai aur saans nahi aa rahi",
        "issue": "Hinglish emergency -- must respond in Roman script",
        "expected_quality": "high -- emergency steps in Hinglish"
    },
]


def query_ollama(prompt: str, system_prompt: str = None) -> dict:
    """Query the SFT model via Ollama."""
    if system_prompt is None:
        system_prompt = "You are Arohan, a medical first aid assistant for elderly Indians. Give clear, numbered first aid steps using simple words."

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 900
        }
    }

    try:
        start = time.time()
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        elapsed = time.time() - start
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}: {resp.text}", "latency": elapsed}
        data = resp.json()
        return {
            "response": data.get("message", {}).get("content", ""),
            "latency": round(elapsed, 2)
        }
    except Exception as e:
        return {"error": str(e), "latency": None}


def query_groq(prompt: str, language: str = "en-IN") -> dict:
    """Query the production Groq model directly (same as llm_service.py does)."""
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY not set", "latency": None}

    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)

    system_prompt = (
        "You are Arohan AI, a calm medical first aid assistant for elderly Indians.\n"
        "Use ONLY English alphabet A-Z. No other scripts allowed.\n"
        "Give 6 to 8 numbered first aid steps using simple words.\n"
        "Never diagnose conditions. Never recommend prescription medications.\n"
        "Always suggest consulting a doctor for serious conditions.\n"
        "For emergencies, always end with: Call 112 or 108 immediately.\n"
        f"LANGUAGE: English"
    )

    try:
        start = time.time()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=900,
        )
        elapsed = time.time() - start
        return {
            "response": response.choices[0].message.content.strip(),
            "latency": round(elapsed, 2)
        }
    except Exception as e:
        return {"error": str(e), "latency": None}


def analyze_issues(response_text: str, query: str) -> list[str]:
    """Flag known bad patterns in the response."""
    issues = []
    text_lower = response_text.lower()

    # Textbook / "refer to section" patterns
    if re.search(r'refer to section|section \d+\.\d+|see section|outlined in section', text_lower):
        issues.append("[TEXTBOOK] References section numbers (trained on bad data)")
    if re.search(r'page \d+|on page', text_lower):
        issues.append("[PAGE-REF] References page numbers (trained on bad data)")
    if re.search(r'this chapter|the chapter|covers the topic', text_lower):
        issues.append("[CHAPTER-REF] References chapters (trained on bad data)")

    # Medical jargon / complex language
    if re.search(r'hemodynamic|tachycardia|vasoconstriction|tissue perfusion|etiology|pathophysiology', text_lower):
        issues.append("[JARGON] Uses complex medical terminology")
    if re.search(r'paramedic|pakistan|punjab medical', text_lower):
        issues.append("[GEOGRAPHY] References Pakistan/Punjab context (bad training data)")

    # Missing key elements
    if 'emergency' not in text_lower and 'unconscious' in query.lower():
        issues.append("[MISSING] No emergency escalation for serious condition")

    # Too short / no numbered steps
    if not re.search(r'\b\d+[)\.]', response_text):
        issues.append("[FORMAT] No numbered steps in response")

    # Language script issues
    if re.search(r'[\u0600-\u06FF]', response_text):  # Arabic/Urdu
        issues.append("[SCRIPT] Contains Urdu/Arabic script (forbidden)")
    if re.search(r'[\u0A80-\u0AFF]', response_text):  # Gujarati
        issues.append("[SCRIPT] Contains Gujarati script (forbidden)")
    if re.search(r'[\u0980-\u09FF]', response_text):  # Bengali
        issues.append("[SCRIPT] Contains Bengali script (forbidden)")

    return issues


def check_emergency_safety(response_text: str) -> list[str]:
    """Check emergency-specific safety requirements."""
    issues = []
    text_lower = response_text.lower()

    if not re.search(r'\b112\b|\b108\b', text_lower):
        issues.append("[SAFETY] Emergency query but no 112/108 mentioned")
    if not re.search(r'call|emergency|ambulance', text_lower):
        issues.append("[SAFETY] No 'call' or 'ambulance' instruction")

    return issues


def run_evaluation():
    results = []

    print("=" * 100)
    print("** Arohan SFT Model vs Groq Production -- Evaluation **")
    print("=" * 100)
    print(f"SFT Model: {OLLAMA_MODEL} (Ollama)")
    print(f"Groq Model: llama-3.3-70b-versatile")
    print()

    for tc in TEST_CASES:
        print("-" * 100)
        print(f"[{tc['id']}] {tc['category']}")
        print(f"Query: {tc['query']}")
        print(f"Issue: {tc['issue']}")
        print(f"Expected quality: {tc['expected_quality']}")
        print()

        # Query both models
        ollama_result = query_ollama(tc['query'])
        groq_result = query_groq(tc['query'])

        # Analyze
        ollama_issues = analyze_issues(ollama_result.get('response', ''), tc['query'])
        groq_issues = analyze_issues(groq_result.get('response', ''), tc['query'])

        # For emergency cases, add safety check
        emergency_keywords = ['unconscious', 'not breathing', 'chest pain', 'behosh', 'saans nahi']
        if any(kw in tc['query'].lower() for kw in emergency_keywords):
            ollama_issues += check_emergency_safety(ollama_result.get('response', ''))
            groq_issues += check_emergency_safety(groq_result.get('response', ''))

        print("--- SFT Model (Ollama) ---")
        print(f"Latency: {ollama_result.get('latency', 'N/A')}s")
        if 'error' in ollama_result:
            print(f"ERROR: {ollama_result['error']}")
        else:
            print(ollama_result.get('response', '')[:800])
        if ollama_issues:
            print("\nIssues found:")
            for iss in ollama_issues:
                print(f"  {iss}")

        print()
        print("--- Groq Production ---")
        print(f"Latency: {groq_result.get('latency', 'N/A')}s")
        if 'error' in groq_result:
            print(f"ERROR: {groq_result['error']}")
        else:
            print(groq_result.get('response', '')[:800])
        if groq_issues:
            print("\nIssues found:")
            for iss in groq_issues:
                print(f"  {iss}")

        print()

        results.append({
            "id": tc['id'],
            "category": tc['category'],
            "query": tc['query'],
            "ollama": {
                "response": ollama_result.get('response', ollama_result.get('error', '')),
                "latency": ollama_result.get('latency'),
                "issues": ollama_issues
            },
            "groq": {
                "response": groq_result.get('response', groq_result.get('error', '')),
                "latency": groq_result.get('latency'),
                "issues": groq_issues
            }
        })

    # --- Summary ---
    print("=" * 100)
    print("** SUMMARY **")
    print("=" * 100)

    sft_issues_total = sum(len(r['ollama']['issues']) for r in results)
    groq_issues_total = sum(len(r['groq']['issues']) for r in results)

    print(f"\nTotal issues flagged:")
    print(f"  SFT Model: {sft_issues_total}")
    print(f"  Groq:     {groq_issues_total}")
    print()

    # Broken down by category
    sft_textbook = sum(1 for r in results for i in r['ollama']['issues'] if 'TEXTBOOK' in i or 'PAGE-REF' in i or 'CHAPTER-REF' in i)
    groq_textbook = sum(1 for r in results for i in r['groq']['issues'] if 'TEXTBOOK' in i or 'PAGE-REF' in i or 'CHAPTER-REF' in i)
    print("Textbook/section reference issues:")
    print(f"  SFT Model: {sft_textbook}")
    print(f"  Groq:     {groq_textbook}")

    sft_jargon = sum(1 for r in results for i in r['ollama']['issues'] if 'JARGON' in i)
    groq_jargon = sum(1 for r in results for i in r['groq']['issues'] if 'JARGON' in i)
    print("\nMedical jargon issues:")
    print(f"  SFT Model: {sft_jargon}")
    print(f"  Groq:     {groq_jargon}")

    sft_geo = sum(1 for r in results for i in r['ollama']['issues'] if 'GEOGRAPHY' in i)
    groq_geo = sum(1 for r in results for i in r['groq']['issues'] if 'GEOGRAPHY' in i)
    print("\nWrong geography references (Pakistan/Punjab):")
    print(f"  SFT Model: {sft_geo}")
    print(f"  Groq:     {groq_geo}")

    sft_format = sum(1 for r in results for i in r['ollama']['issues'] if 'FORMAT' in i)
    groq_format = sum(1 for r in results for i in r['groq']['issues'] if 'FORMAT' in i)
    print("\nMissing numbered steps:")
    print(f"  SFT Model: {sft_format}")
    print(f"  Groq:     {groq_format}")

    sft_safety = sum(1 for r in results for i in r['ollama']['issues'] if 'SAFETY' in i)
    groq_safety = sum(1 for r in results for i in r['groq']['issues'] if 'SAFETY' in i)
    print("\nSafety concerns (no 112/108):")
    print(f"  SFT Model: {sft_safety}")
    print(f"  Groq:     {groq_safety}")

    # Save results
    report_path = Path(__file__).resolve().parents[1] / "sft_vs_groq_eval_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nFull report saved to: {report_path}")


if __name__ == "__main__":
    run_evaluation()
