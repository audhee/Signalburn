"""
step5_evaluate_comprehensive.py — Comprehensive Model Evaluation

Compares 4 models on curated first aid queries:
  1. Groq Production (llama-3.3-70b-versatile) — the current live model
  2. Base Llama 3 8B (no fine-tuning)
  3. QLoRA SFT-tuned (Amulya's adapter)
  4. QLoRA + DPO (Anisha's alignment on top of Amulya's adapter)

Usage (local):
    python step5_evaluate_comprehensive.py

Usage (Colab with all models):
    python step5_evaluate_comprehensive.py --qlora-adapter /path/to/arohan_qlora_adapter
                                         --dpo-adapter /path/to/arohan_dpo_adapter

Output:
    ./evals/comprehensive_eval_report.json
    Console: Comparison table with scores
"""

import os
import sys
import json
import time
import torch
import logging
import argparse
import requests
import re
from pathlib import Path
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(os.path.dirname(BASE_DIR), "evals")

# --- Test Queries ------------------------------------------------------------
# 20 diverse test cases covering all key first aid scenarios

TEST_CASES = [
    # Standard first aid queries
    {"id": "bleeding-cut", "query": "My father has a small bleeding cut on his hand. What first aid should I do?",
     "emergency": False, "expected_112": False, "language": "English"},
    {"id": "nosebleed", "query": "My nose is bleeding suddenly. What should I do?",
     "emergency": False, "expected_112": True, "language": "English"},
    {"id": "burn-oil", "query": "I got a burn from hot oil while cooking. What should I do?",
     "emergency": False, "expected_112": False, "language": "English"},
    {"id": "fainting", "query": "A person fainted and is not responding. What first aid should I give?",
     "emergency": True, "expected_112": True, "language": "English"},
    {"id": "heart-attack", "query": "My mother has chest pain and is not breathing properly.",
     "emergency": True, "expected_112": True, "language": "English"},
    {"id": "choking", "query": "Someone is choking on food and cannot speak. What should I do?",
     "emergency": True, "expected_112": True, "language": "English"},
    {"id": "snake-bite", "query": "A snake bit me on my leg while walking in the field. What should I do?",
     "emergency": True, "expected_112": True, "language": "English"},
    {"id": "dog-bite", "query": "A stray dog bit my son's hand. What first aid should I do?",
     "emergency": False, "expected_112": False, "language": "English"},
    {"id": "seizure", "query": "My brother is having a seizure (fits). What should I do?",
     "emergency": True, "expected_112": True, "language": "English"},
    {"id": "head-injury", "query": "An elderly person fell and hit their head. What should I do?",
     "emergency": True, "expected_112": True, "language": "English"},
    {"id": "poisoning", "query": "My child swallowed some cleaning liquid. What should I do?",
     "emergency": True, "expected_112": True, "language": "English"},
    {"id": "fever", "query": "My elderly mother has a high fever of 103 degrees. What should I do?",
     "emergency": False, "expected_112": True, "language": "English"},
    {"id": "allergic-reaction", "query": "I ate something and my face is swelling up. I am having trouble breathing.",
     "emergency": True, "expected_112": True, "language": "English"},
    {"id": "electric-shock", "query": "Someone touched a live wire and got an electric shock. What should I do?",
     "emergency": True, "expected_112": True, "language": "English"},
    # Multilingual queries
    {"id": "hindi-arm-pain", "query": "Mera haath bahut dard kar raha hai. Kya karna chahiye?",
     "emergency": False, "expected_112": False, "language": "Hinglish"},
    {"id": "kannada-fever", "query": "Nanna amma ge jvara bandide. Enu madabeku?",
     "emergency": False, "expected_112": False, "language": "Kanglish"},
    {"id": "hinglish-emergency", "query": "Mera bhai behosh hai aur saans nahi aa rahi",
     "emergency": True, "expected_112": True, "language": "Hinglish"},
    {"id": "hindi-burn", "query": "Garami tel se haath jal gaya hai. Kya karein?",
     "emergency": False, "expected_112": False, "language": "Hinglish"},
    {"id": "kannada-cut", "query": "Kai ge gaya aagide. Rakta bartide. Enu madabeku?",
     "emergency": False, "expected_112": False, "language": "Kanglish"},
    # Multi-query comprehension
    {"id": "multi-symptom", "query": "My father fell in the bathroom, his arm is bleeding and he cannot move his leg.",
     "emergency": True, "expected_112": True, "language": "English"},
]

LANGUAGE_SCRIPT_RULES = {
    "English": r'^[A-Za-z0-9\s\.,!?;\'\"\-\(\)]+$',
    "Hinglish": r'^[A-Za-z0-9\s\.,!?;\'\"\-\(\)]+$',  # Roman script
    "Kanglish": r'^[A-Za-z0-9\s\.,!?;\'\"\-\(\)]+$',   # Roman script
}


# --- Scoring Functions -------------------------------------------------------

def count_first_aid_steps(text: str) -> int:
    """Count numbered first aid steps in response."""
    numbered = re.findall(r'(?:^|\n)\s*\d+[\.\)]\s*', text)
    return len(numbered)


def has_emergency_number(text: str) -> bool:
    """Check if response mentions emergency numbers."""
    return bool(re.search(r'\b112\b|\b108\b', text))


def has_call_instruction(text: str) -> bool:
    """Check if response tells user to call for help."""
    return bool(re.search(r'\bcall\b|\bphone\b|\bdial\b|\bcall\b', text.lower()))


def has_no_diagnosis(text: str) -> bool:
    """Check text does not contain diagnosing language ('you have X disease')."""
    diagnosis_patterns = [
        r'\byou have\s+\w+\s+(disease|condition|syndrome)\b',
        r'\bdiagnosed with\b',
        r'\byou are suffering from\b',
    ]
    return not any(re.search(p, text.lower()) for p in diagnosis_patterns)


def has_simple_language(text: str) -> bool:
    """Check for medical jargon that should not be in responses."""
    jargon = [
        'hemodynamic', 'tachycardia', 'vasoconstriction', 'tissue perfusion',
        'etiology', 'pathophysiology', 'hypovolemic', 'myocardial infarction',
        'cerebrovascular', 'thrombus', 'embolism', 'ischemia', 'necrosis',
        'refer to section', 'section \\d+\\.\\d+', 'outlined in section',
        'the chapter', 'as discussed in',
    ]
    # Score: 0 jargon words = 1.0, each jargon word reduces by 0.2
    jargon_count = 0
    for j in jargon:
        if re.search(j, text.lower()):
            jargon_count += 1
    return max(0, 1.0 - (jargon_count * 0.2))


def check_script_purity(text: str, language: str) -> float:
    """Check that the response uses the correct script."""
    if language in ["English", "Hinglish", "Kanglish"]:
        # Should only contain Roman alphabet
        forbidden = re.compile(r'[\u0900-\u097F\u0C80-\u0CFF\u0600-\u06FF\u0980-\u09FF\u0B00-\u0B7F\u0B80-\u0BFF\u0C00-\u0C7F\u4E00-\u9FFF]')
        if forbidden.search(text):
            return 0.0
        return 1.0
    return 1.0


def score_response(response: str, test_case: Dict) -> Dict:
    """Score a single response on multiple quality dimensions."""
    text_lower = response.lower()

    # Dimension 1: Numbered first aid steps
    steps_count = count_first_aid_steps(response)
    steps_score = min(steps_count / 4, 1.0)  # Expect at least 4 steps

    # Dimension 2: Emergency number mention
    emergency_score = 1.0 if has_emergency_number(response) else (
        0.0 if test_case["expected_112"] else 1.0
    )

    # Dimension 3: Call instruction
    call_score = 1.0 if has_call_instruction(response) else 0.5

    # Dimension 4: No diagnosis
    diagnosis_score = 1.0 if has_no_diagnosis(response) else 0.3

    # Dimension 5: Simple language (no medical jargon)
    jargon_score = has_simple_language(response)

    # Dimension 6: Script purity
    script_score = check_script_purity(response, test_case["language"])

    # Dimension 7: Response has substance (not too short)
    length_score = min(len(response) / 200, 1.0)

    # Overall score (weighted average)
    weights = {
        "steps": 0.25,
        "emergency": 0.20,
        "call": 0.10,
        "diagnosis": 0.15,
        "jargon": 0.10,
        "script": 0.10,
        "length": 0.10,
    }

    overall = (
        steps_score * weights["steps"] +
        emergency_score * weights["emergency"] +
        call_score * weights["call"] +
        diagnosis_score * weights["diagnosis"] +
        jargon_score * weights["jargon"] +
        script_score * weights["script"] +
        length_score * weights["length"]
    )

    return {
        "overall_score": round(overall, 3),
        "dimensions": {
            "numbered_steps": round(steps_score, 3),
            "emergency_number": round(emergency_score, 3),
            "call_instruction": round(call_score, 3),
            "no_diagnosis": round(diagnosis_score, 3),
            "simple_language": round(jargon_score, 3),
            "script_purity": round(script_score, 3),
            "response_length": round(length_score, 3),
        }
    }


# --- Model Query Functions ---------------------------------------------------

def query_ollama(prompt: str, model_name: str = "arohan-medical") -> Dict:
    """Query a model via Ollama."""
    try:
        start = time.time()
        resp = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are Arohan, a medical first aid assistant for elderly Indians."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 900}
            },
            timeout=30
        )
        elapsed = time.time() - start
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}", "latency": elapsed}
        data = resp.json()
        return {"response": data.get("message", {}).get("content", ""), "latency": round(elapsed, 2)}
    except Exception as e:
        return {"error": str(e), "latency": None}


def query_groq(prompt: str) -> Dict:
    """Query Groq production model."""
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        return {"error": "GROQ_API_KEY not set", "latency": None}
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        start = time.time()
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are Arohan, a medical first aid assistant for elderly Indians. Give clear, numbered first aid steps using simple words."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=900,
        )
        elapsed = time.time() - start
        return {"response": resp.choices[0].message.content.strip(), "latency": round(elapsed, 2)}
    except Exception as e:
        return {"error": str(e), "latency": None}


def query_local_model(prompt: str, adapter_path: str = None, merged_path: str = None) -> Dict:
    """Query a locally loaded model (QLoRA or QLoRA+DPO)."""
    try:
        from unsloth import FastLanguageModel
        from peft import PeftModel

        if merged_path:
            model, tokenizer = FastLanguageModel.from_pretrained(
                model_name=merged_path,
                max_seq_length=2048,
                load_in_4bit=False,
            )
        else:
            model, tokenizer = FastLanguageModel.from_pretrained(
                model_name="unsloth/llama-3-8b-Instruct-bnb-4bit",
                max_seq_length=2048,
                load_in_4bit=True,
            )
            if adapter_path:
                model = PeftModel.from_pretrained(model, adapter_path)

        FastLanguageModel.for_inference(model)

        messages = [
            {"role": "system", "content": "You are Arohan, a medical first aid assistant for elderly Indians."},
            {"role": "user", "content": prompt},
        ]
        formatted = tokenizer.apply_chat_template(messages, tokenize=False)
        formatted += "<|start_header_id|>assistant<|end_header_id|>\n\n"

        inputs = tokenizer(formatted, return_tensors="pt").to(model.device)

        start = time.time()
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=400,
                temperature=0.1,
                do_sample=True,
                top_p=0.9,
            )
        elapsed = time.time() - start

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        if "assistant" in response:
            response = response.split("assistant")[-1].strip()

        return {"response": response, "latency": round(elapsed, 2)}

    except Exception as e:
        return {"error": f"Local model error: {e}", "latency": None}


# --- Evaluation Runner -------------------------------------------------------

def evaluate_all_models(args):
    """Run full evaluation across all available models."""
    results = []

    print("\n" + "=" * 80)
    print("  COMPREHENSIVE MODEL EVALUATION — Arohan First Aid")
    print("=" * 80)
    print(f"  Test cases: {len(TEST_CASES)}")
    print()

    # Determine which models are available
    models = {}

    # Model 1: Groq (always try)
    if args.groq or args.all:
        models["Groq Production (llama-3.3-70b)"] = lambda q: query_groq(q)

    # Model 2: QLoRA adapter
    if args.qlora_adapter and os.path.exists(args.qlora_adapter):
        adapter = args.qlora_adapter
        models[f"QLoRA (SFT)"] = lambda q, a=adapter: query_local_model(q, adapter_path=a)

    # Model 3: QLoRA + DPO adapter
    if args.dpo_adapter and os.path.exists(args.dpo_adapter):
        adapter = args.dpo_adapter
        models[f"QLoRA + DPO"] = lambda q, a=adapter: query_local_model(q, adapter_path=a)

    # Model 4: Ollama SFT
    models["Ollama SFT (base)"] = lambda q: query_ollama(q, "arohan-medical")

    if not models:
        logger.error("No models available. Use --groq, --qlora-adapter, --dpo-adapter, or --all.")
        sys.exit(1)

    logger.info(f"Models to evaluate: {list(models.keys())}")
    logger.info(f"\nRunning {len(TEST_CASES)} test cases across {len(models)} models...\n")

    # Run each test case
    for tc in TEST_CASES:
        logger.info(f"[{tc['id']}] {tc['query'][:60]}...")

        model_results = {}
        for model_name, query_fn in models.items():
            result = query_fn(tc["query"])
            model_results[model_name] = result

            if "error" not in result:
                scores = score_response(result["response"], tc)
                model_results[model_name]["scores"] = scores
                model_results[model_name]["steps_count"] = count_first_aid_steps(result["response"])
                model_results[model_name]["has_112"] = has_emergency_number(result["response"])

        results.append({
            "test_case": tc,
            "model_results": model_results,
        })

        # Show quick summary line
        scores_line = []
        for name, res in model_results.items():
            if "scores" in res:
                scores_line.append(f"{name[:12]}: {res['scores']['overall_score']:.2f}")
        logger.info(f"  Scores: {' | '.join(scores_line)}")

    # Generate summary
    summary = generate_summary(results, models)

    # Save report
    report_path = os.path.join(OUTPUT_DIR, "comprehensive_eval_report.json")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "summary": summary}, f, indent=2, ensure_ascii=False)

    # Print final report
    print_summary(summary, results)

    return results, summary


def generate_summary(results: List[Dict], models: Dict) -> Dict:
    """Generate summary statistics from evaluation results."""
    summary = {}

    for model_name in models.keys():
        scores = []
        steps_counts = []
        has_112_count = 0
        total_cases = 0
        errors = 0
        latencies = []

        for case_result in results:
            mr = case_result["model_results"].get(model_name, {})
            if "error" in mr:
                errors += 1
                continue

            if "scores" in mr:
                scores.append(mr["scores"]["overall_score"])
                steps_counts.append(mr.get("steps_count", 0))
                if mr.get("has_112", False):
                    has_112_count += 1
                total_cases += 1

            if mr.get("latency"):
                latencies.append(mr["latency"])

        avg_score = sum(scores) / len(scores) if scores else 0
        avg_steps = sum(steps_counts) / len(steps_counts) if steps_counts else 0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0

        # Count scoring breakdowns
        excellent = sum(1 for s in scores if s >= 0.8)
        good = sum(1 for s in scores if 0.6 <= s < 0.8)
        poor = sum(1 for s in scores if s < 0.6)

        summary[model_name] = {
            "avg_overall_score": round(avg_score, 3),
            "avg_steps_per_response": round(avg_steps, 1),
            "has_112_in_emergencies": f"{has_112_count}/{total_cases}",
            "has_112_ratio": round(has_112_count / total_cases if total_cases else 0, 3),
            "avg_latency_seconds": round(avg_latency, 2),
            "p95_latency_seconds": round(p95_latency, 2),
            "errors": errors,
            "cases_tested": total_cases,
            "scoring_breakdown": {
                "excellent (>= 0.8)": excellent,
                "good (0.6 - 0.8)": good,
                "poor (< 0.6)": poor,
            }
        }

    return summary


def print_summary(summary: Dict, results: List[Dict]):
    """Print a formatted summary to console."""
    print("\n" + "=" * 80)
    print("  FINAL EVALUATION REPORT — Arohan Model Comparison")
    print("=" * 80)

    # Model comparison table
    print(f"\n{'Model':<35} {'Score':<8} {'Steps':<8} {'112/Emerg':<12} {'Latency':<10}")
    print("-" * 75)

    for model_name, stats in sorted(summary.items(), key=lambda x: -x[1]["avg_overall_score"]):
        score = stats["avg_overall_score"]
        steps = stats["avg_steps_per_response"]
        emerg = stats["has_112_in_emergencies"]
        lat = stats["avg_latency_seconds"]
        print(f"{model_name:<35} {score:<8.3f} {steps:<8.1f} {emerg:<12} {lat:<10.2f}s")

    print()
    print("  Detailed Breakdown:")
    print()

    for model_name, stats in sorted(summary.items(), key=lambda x: -x[1]["avg_overall_score"]):
        print(f"  [{model_name}]")
        print(f"    Avg Score:          {stats['avg_overall_score']:.3f}")
        print(f"    Avg Steps/Response: {stats['avg_steps_per_response']:.1f}")
        print(f"    112 in Emergencies: {stats['has_112_in_emergencies']}")
        print(f"    Avg Latency:        {stats['avg_latency_seconds']:.2f}s")
        print(f"    Cases Tested:       {stats['cases_tested']}")
        print(f"    Errors:             {stats['errors']}")
        bd = stats["scoring_breakdown"]
        print(f"    Excellent (>=0.8):  {bd['excellent (>= 0.8)']} cases")
        print(f"    Good (0.6-0.8):     {bd['good (0.6 - 0.8)']} cases")
        print(f"    Poor (<0.6):        {bd['poor (< 0.6)']} cases")
        print()

    # Find best model
    best_model = max(summary.items(), key=lambda x: x[1]["avg_overall_score"])
    print(f"  BEST MODEL: {best_model[0]} (score: {best_model[1]['avg_overall_score']:.3f})")

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Arohan Comprehensive Model Evaluation")
    parser.add_argument("--qlora-adapter", type=str, default=None,
                       help="Path to QLoRA SFT-trained adapter")
    parser.add_argument("--dpo-adapter", type=str, default=None,
                       help="Path to QLoRA + DPO adapter")
    parser.add_argument("--groq", action="store_true",
                       help="Include Groq production comparison")
    parser.add_argument("--all", action="store_true",
                       help="Try all models (requires adapters to be available)")

    # For local evaluation without loading models
    parser.add_argument("--offline", action="store_true",
                       help="Run evaluation using saved responses only (no model loading)")

    args = parser.parse_args()

    if not args.qlora_adapter and not args.dpo_adapter and not args.groq and not args.all and not args.offline:
        # Default: just test Groq and Ollama
        args.groq = True
        logger.info("No adapters specified. Defaulting to Groq + Ollama comparison.")

    evaluate_all_models(args)

    print(f"\n  Report saved to: {os.path.join(OUTPUT_DIR, 'comprehensive_eval_report.json')}")
    print()


if __name__ == "__main__":
    main()
