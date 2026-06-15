"""run_full_demo.py - One-command fine-tuning demo for Arohan
==========================================================

Runs the entire dataset pipeline + demo queries in one go.

Usage (from repo root):
    python backend/sft_tuning/run_full_demo.py

No GPU required. Completes in roughly 30 seconds.
"""

import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from textwrap import dedent

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
SFT_DATA   = SCRIPT_DIR / "sft_data"
TRAIN_FILE = SFT_DATA / "sft_dataset_train.jsonl"
VAL_FILE   = SFT_DATA / "sft_dataset_val.jsonl"
RAW_PAIRS  = SFT_DATA / "sft_pairs_raw.jsonl"


def banner(step, title):
    sep = """===""" * 23
    print()
    print(sep)
    print("  STEP ", step, ": ", title, sep="")
    print(sep)
    print()


def run(script_name):
    script_path = SCRIPT_DIR / script_name
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(SCRIPT_DIR.parent.parent),
    )
    if result.returncode != 0:
        raise SystemExit("FAILED: " + script_name + " (exit code " + str(result.returncode) + ")")


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def cosine_score(q_tokens, i_tokens):
    common = set(q_tokens) & set(i_tokens)
    dot = sum(q_tokens[t] * i_tokens[t] for t in common)
    qn = math.sqrt(sum(v * v for v in q_tokens.values()))
    in_ = math.sqrt(sum(v * v for v in i_tokens.values()))
    if qn == 0 or in_ == 0:
        return 0.0
    return dot / (qn * in_)


def run_demo_queries():
    queries = [
        "What is malaria?",
        "How to treat a burn?",
        "What are the symptoms of diabetes?",
        "Someone had a stroke, what should I do?",
        "How is tuberculosis treated?",
    ]

    if not RAW_PAIRS.exists():
        print("  WARNING: sft_pairs_raw.jsonl not found")
        return

    rows = []
    with RAW_PAIRS.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get("source", "").startswith("sashwat_chroma/"):
                rows.append(item)

    print("  Loaded ", len(rows), " Sashwat-only SFT pairs")
    print()

    for i, query in enumerate(queries, 1):
        q_tokens = Counter(tokenize(query))
        best_score = -1.0
        best = {}
        q_norm = " ".join(tokenize(query))

        for item in rows:
            inst = item.get("instruction", "")
            inst_norm = " ".join(tokenize(inst))
            sc = cosine_score(q_tokens, Counter(tokenize(inst))) * 0.85
            sc += cosine_score(q_tokens, Counter(tokenize(item.get("output", "")))) * 0.15
            if q_norm == inst_norm:
                sc += 2.0
            elif q_norm in inst_norm or inst_norm in q_norm:
                sc += 1.0
            if sc > best_score:
                best_score, best = sc, item

        instr = best.get("instruction", "")
        score_str = str(round(best_score, 3))
        output = best.get("output", "")
        short_output = output[:120]
        if len(output) > 120:
            short_output = short_output + "..."
        print("  [" + str(i) + "] Q: " + query)
        print("      Match: " + instr + "  (score " + score_str + ")")
        print("      A: " + short_output)
        print()


def dataset_stats():
    stats = {"train": 0, "val": 0, "sources": set()}
    for path, key in [(TRAIN_FILE, "train"), (VAL_FILE, "val")]:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                stats[key] += 1
                try:
                    row = json.loads(line)
                    src = row.get("source", "unknown").split("/")[0]
                    stats["sources"].add(src)
                except json.JSONDecodeError:
                    pass
    return stats


def main():
    print("""
=============================================
  Arohan Fine-Tuning Demo - Full Pipeline
  Extract -> SFT Pairs -> Train/Val -> Demo
=============================================""")
    print()

    banner(1, "Extract RAG chunks from Sashwat ChromaDB")
    run("step1_extract_rag_data.py")

    banner(2, "Generate SFT instruction/output pairs")
    run("step2b_generate_sft_pairs_from_sashwat_chunks.py")

    banner(3, "Prepare train/val splits (Llama 3 chat template)")
    run("step3_prepare_dataset.py")

    banner(4, "Verify all sources are sashwat_chroma only")
    run("verify_sashwat_only.py")

    banner(5, "Demo: Run sample medical queries against SFT dataset")
    run_demo_queries()

    stats = dataset_stats()
    print("=" * 70)
    print("  DEMO COMPLETE")
    print("=" * 70)
    print("  Training pairs:   " + str(stats["train"]))
    print("  Validation pairs: " + str(stats["val"]))
    print("  Total:            " + str(stats["train"] + stats["val"]))
    print("  Sources:          " + (", ".join(stats["sources"]) or "N/A"))
    print("  Data location:    " + str(SFT_DATA))
    print()
    print("  Next step (requires GPU - Google Colab free tier):")
    print("    1. Upload sft_data/ to Google Drive")
    print("    2. Open upload_arohan/colab_arohan_pipeline.ipynb in Colab")
    print("    3. Run all cells - QLoRA training takes 15-20 min on T4")
    print("=" * 70)


if __name__ == "__main__":
    main()
