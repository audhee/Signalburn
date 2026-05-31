"""
demo_sashwat_query.py

Reliable meeting demo for querying the Sashwat-only SFT dataset.

This does not claim to be model inference. It shows the exact instruction-output
pairs prepared from Sashwat's RAG database and returns the closest answer from
that Sashwat-only dataset.

Usage:
  python backend/sft_tuning/demo_sashwat_query.py "What is malaria?"
"""

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parent / "sft_data" / "sft_pairs_raw.jsonl"


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def cosine_score(query_tokens: Counter, item_tokens: Counter) -> float:
    common = set(query_tokens) & set(item_tokens)
    dot = sum(query_tokens[token] * item_tokens[token] for token in common)
    query_norm = math.sqrt(sum(value * value for value in query_tokens.values()))
    item_norm = math.sqrt(sum(value * value for value in item_tokens.values()))
    if query_norm == 0 or item_norm == 0:
        return 0.0
    return dot / (query_norm * item_norm)


def load_dataset() -> list[dict]:
    if not DATA_FILE.exists():
        raise SystemExit(f"Dataset not found: {DATA_FILE}. Run step1, step2b, and step3 first.")

    rows = []
    with DATA_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            item = json.loads(line)
            source = item.get("source", "")
            if not source.startswith("sashwat_chroma/"):
                continue
            rows.append(item)
    return rows


def normalize(text: str) -> str:
    return " ".join(tokenize(text))


def find_best_answer(query: str, rows: list[dict]) -> tuple[float, dict]:
    query_tokens = Counter(tokenize(query))
    query_norm = normalize(query)
    best_score = -1.0
    best_item = {}

    for item in rows:
        instruction = item.get("instruction", "")
        instruction_norm = normalize(instruction)
        instruction_score = cosine_score(query_tokens, Counter(tokenize(instruction)))
        answer_score = cosine_score(query_tokens, Counter(tokenize(item.get("output", ""))))
        score = (instruction_score * 0.85) + (answer_score * 0.15)
        if query_norm == instruction_norm:
            score += 2.0
        elif query_norm in instruction_norm or instruction_norm in query_norm:
            score += 1.0
        if score > best_score:
            best_score = score
            best_item = item

    return best_score, best_item


def main() -> None:
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        query = input("Enter medical query: ").strip()

    rows = load_dataset()
    score, item = find_best_answer(query, rows)

    print("\nSashwat-only query demo")
    print("=" * 60)
    print(f"User query: {query}")
    print(f"Dataset rows searched: {len(rows)}")
    print(f"Source: {item.get('source', 'unknown')}")
    print(f"Match score: {score:.3f}")
    print("\nClosest SFT instruction:")
    print(item.get("instruction", ""))
    print("\nResponse from Sashwat-only prepared data:")
    print(item.get("output", ""))
    print("=" * 60)
    print("Note: This is dataset retrieval demo, not final model inference.")


if __name__ == "__main__":
    main()
