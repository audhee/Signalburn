"""
step3_prepare_dataset.py — Validate, clean, deduplicate, and format the SFT dataset.
Converts raw Q&A pairs into the Llama 3 chat template format ready for training.

Usage:
    python step3_prepare_dataset.py

Input:
    ./sft_data/sft_pairs_raw.jsonl

Output:
    ./sft_data/sft_dataset_train.jsonl  — Training split (90%)
    ./sft_data/sft_dataset_val.jsonl    — Validation split (10%)
    ./sft_data/dataset_stats.json       — Dataset statistics
"""

import os
import sys
import json
import hashlib
import random
import logging
import re
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────
INPUT_FILE      = os.path.join(os.path.dirname(__file__), "sft_data", "sft_pairs_raw.jsonl")
TRAIN_FILE      = os.path.join(os.path.dirname(__file__), "sft_data", "sft_dataset_train.jsonl")
VAL_FILE        = os.path.join(os.path.dirname(__file__), "sft_data", "sft_dataset_val.jsonl")
STATS_FILE      = os.path.join(os.path.dirname(__file__), "sft_data", "dataset_stats.json")
ALPACA_FILE     = os.path.join(os.path.dirname(__file__), "sft_data", "sft_dataset_alpaca.json")

TRAIN_SPLIT     = 0.9
RANDOM_SEED     = 42

# Quality filters
MIN_QUESTION_LEN = 15
MAX_QUESTION_LEN = 500
MIN_ANSWER_LEN   = 50
MAX_ANSWER_LEN   = 2000

# Arohan system prompt (must match what Arohan uses in production)
AROHAN_SYSTEM_PROMPT = (
    "You are Arohan, a medical first aid assistant for elderly Indians. "
    "Provide clear, numbered first aid steps using simple words. "
    "Never diagnose conditions. Never recommend prescription medications. "
    "Always suggest consulting a doctor for serious or worsening conditions. "
    "For emergencies, always end with: Call 112 or 108 immediately."
)


def load_raw_pairs(filepath: str) -> List[Dict]:
    """Load raw Q&A pairs from JSONL."""
    if not os.path.exists(filepath):
        logger.error(f"Input file not found: {filepath}")
        logger.error("Run step2_generate_sft_pairs.py first!")
        sys.exit(1)

    pairs = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    pairs.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON on line {line_num}, skipping")

    logger.info(f"Loaded {len(pairs)} raw pairs from {filepath}")
    return pairs


def clean_text(text: str) -> str:
    """Clean up Q&A text artifacts."""
    # Remove leading/trailing whitespace and quotes
    text = text.strip().strip('"').strip("'")

    # Fix double spaces
    text = re.sub(r' {2,}', ' ', text)

    # Fix broken newlines
    text = text.replace("\\n", "\n")

    # Remove any LLM meta-commentary
    for prefix in ["Here's", "Here is", "Sure,", "Of course,", "Based on"]:
        if text.startswith(prefix) and "\n" in text:
            # Keep from the first newline onwards (skip preamble)
            first_newline = text.index("\n")
            potential = text[first_newline:].strip()
            if len(potential) > MIN_ANSWER_LEN:
                text = potential

    return text.strip()


def is_quality_pair(pair: Dict) -> bool:
    """Check if a Q&A pair meets quality standards."""
    question = pair.get("instruction", "")
    answer   = pair.get("output", "")

    # Length checks
    if len(question) < MIN_QUESTION_LEN or len(question) > MAX_QUESTION_LEN:
        return False
    if len(answer) < MIN_ANSWER_LEN or len(answer) > MAX_ANSWER_LEN:
        return False

    # Must end with ? or be a valid question
    question_lower = question.lower()
    is_question = (
        question.endswith("?") or
        any(question_lower.startswith(w) for w in [
            "what", "how", "when", "why", "where", "which",
            "can", "should", "is", "are", "do", "does",
            "explain", "describe", "tell", "list"
        ])
    )
    if not is_question:
        return False

    # Answer should not be a refusal
    refusal_patterns = [
        "i cannot", "i can't", "i'm not able", "as an ai",
        "i don't have", "i'm sorry but"
    ]
    answer_lower = answer.lower()
    if any(p in answer_lower for p in refusal_patterns):
        return False

    return True


def deduplicate(pairs: List[Dict]) -> List[Dict]:
    """Remove duplicate or near-duplicate Q&A pairs."""
    seen_hashes = set()
    unique_pairs = []

    for pair in pairs:
        # Hash based on normalized question text
        question_normalized = re.sub(r'\s+', ' ', pair["instruction"].lower().strip())
        q_hash = hashlib.md5(question_normalized.encode()).hexdigest()

        if q_hash not in seen_hashes:
            seen_hashes.add(q_hash)
            unique_pairs.append(pair)

    removed = len(pairs) - len(unique_pairs)
    if removed:
        logger.info(f"Removed {removed} duplicate pairs")

    return unique_pairs


def format_llama3_chat(instruction: str, output: str) -> str:
    """Format as Llama 3 Instruct chat template."""
    return (
        f"<|begin_of_text|>"
        f"<|start_header_id|>system<|end_header_id|>\n\n"
        f"{AROHAN_SYSTEM_PROMPT}<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n"
        f"{instruction}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
        f"{output}<|eot_id|>"
    )


def prepare_dataset(pairs: List[Dict]) -> List[Dict]:
    """Full pipeline: clean → filter → dedup → format."""

    # Step 1: Clean text
    logger.info("Cleaning text...")
    for pair in pairs:
        pair["instruction"] = clean_text(pair.get("instruction", ""))
        pair["output"] = clean_text(pair.get("output", ""))

    # Step 2: Quality filter
    logger.info("Filtering for quality...")
    quality_pairs = [p for p in pairs if is_quality_pair(p)]
    logger.info(f"Quality filter: {len(pairs)} → {len(quality_pairs)} pairs")

    # Step 3: Deduplicate
    logger.info("Deduplicating...")
    unique_pairs = deduplicate(quality_pairs)
    logger.info(f"After dedup: {len(unique_pairs)} pairs")

    # Step 4: Add Llama 3 formatted text
    logger.info("Formatting for Llama 3 chat template...")
    for pair in unique_pairs:
        pair["text"] = format_llama3_chat(pair["instruction"], pair["output"])

    return unique_pairs


def split_and_save(pairs: List[Dict]):
    """Split into train/val and save all formats."""
    random.seed(RANDOM_SEED)
    random.shuffle(pairs)

    split_idx = int(len(pairs) * TRAIN_SPLIT)
    train_set = pairs[:split_idx]
    val_set   = pairs[split_idx:]

    # Save JSONL format (for Unsloth/TRL SFTTrainer)
    for filepath, dataset in [(TRAIN_FILE, train_set), (VAL_FILE, val_set)]:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            for item in dataset:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # Save Alpaca JSON format (alternative training format)
    alpaca_data = [{
        "instruction": p["instruction"],
        "input": p.get("input", ""),
        "output": p["output"]
    } for p in train_set]

    with open(ALPACA_FILE, "w", encoding="utf-8") as f:
        json.dump(alpaca_data, f, indent=2, ensure_ascii=False)

    # Save statistics
    stats = {
        "total_pairs": len(pairs),
        "train_size": len(train_set),
        "val_size": len(val_set),
        "avg_question_length": sum(len(p["instruction"]) for p in pairs) / len(pairs) if pairs else 0,
        "avg_answer_length": sum(len(p["output"]) for p in pairs) / len(pairs) if pairs else 0,
        "sources": {},
    }
    for p in pairs:
        src = p.get("source", "unknown")
        stats["sources"][src] = stats["sources"].get(src, 0) + 1

    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    return train_set, val_set, stats


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Step 3: Prepare & Format SFT Dataset")
    print("=" * 60 + "\n")

    raw_pairs = load_raw_pairs(INPUT_FILE)
    clean_pairs = prepare_dataset(raw_pairs)
    train_set, val_set, stats = split_and_save(clean_pairs)

    print("\n" + "=" * 60)
    print("  DATASET PREPARATION COMPLETE")
    print("=" * 60)
    print(f"  Total quality pairs:   {stats['total_pairs']}")
    print(f"  Training set:          {stats['train_size']}")
    print(f"  Validation set:        {stats['val_size']}")
    print(f"  Avg question length:   {stats['avg_question_length']:.0f} chars")
    print(f"  Avg answer length:     {stats['avg_answer_length']:.0f} chars")
    print(f"\n  Output files:")
    print(f"    Train JSONL: {TRAIN_FILE}")
    print(f"    Val JSONL:   {VAL_FILE}")
    print(f"    Alpaca JSON: {ALPACA_FILE}")
    print("=" * 60 + "\n")
    print("[DONE] Next step: Upload sft_data/ folder to Google Drive,")
    print("   then run step4_sft_train_colab.py on Google Colab")
