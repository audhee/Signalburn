"""
step2b_generate_sft_pairs_from_sashwat_chunks.py

Generate SFT Q&A pairs ONLY from Sashwat's extracted Chroma chunks.

Design goal:
- Stay "Sashwat-only" (no Harshita/Geshna/other local KB sources).
- Avoid LLM calls (deterministic).
- Only emit pairs when the chunk clearly contains a Q/A pattern.

Input:
  ./sft_data/raw_chunks.jsonl   (from step1_extract_rag_data.py)

Output:
  ./sft_data/sft_pairs_raw.jsonl  (overwrites by default; pass --out to change)

Usage:
  python step2b_generate_sft_pairs_from_sashwat_chunks.py
  python step2b_generate_sft_pairs_from_sashwat_chunks.py --min-answer-chars 60
"""

import os
import re
import json
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "sft_data"

DEFAULT_INFILE = DATA_DIR / "raw_chunks.jsonl"
DEFAULT_OUTFILE = DATA_DIR / "sft_pairs_raw.jsonl"


QA_PATTERNS = [
    # "Question: ... Answer: ..."
    re.compile(r"(?is)\bQuestion\s*:\s*(?P<q>.+?)\s*\bAnswer\s*:\s*(?P<a>.+?)\s*$"),
    # "Q: ... A: ..."
    re.compile(r"(?is)\bQ\s*:\s*(?P<q>.+?)\s*\bA\s*:\s*(?P<a>.+?)\s*$"),
]


def _clean(text: str) -> str:
    text = (text or "").strip()
    # collapse excessive whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_qa(text: str):
    t = _clean(text)
    for pat in QA_PATTERNS:
        m = pat.match(t)
        if not m:
            continue
        q = _clean(m.group("q"))
        a = _clean(m.group("a"))
        if q and a:
            return q, a
    return None


def main():
    parser = argparse.ArgumentParser(description="Generate SFT pairs from Sashwat raw chunks (Q/A only).")
    parser.add_argument("--in", dest="infile", default=str(DEFAULT_INFILE), help="Input raw_chunks.jsonl path")
    parser.add_argument("--out", dest="outfile", default=str(DEFAULT_OUTFILE), help="Output sft_pairs_raw.jsonl path")
    parser.add_argument("--min-question-chars", type=int, default=15, help="Minimum question length")
    parser.add_argument("--min-answer-chars", type=int, default=60, help="Minimum answer length")
    args = parser.parse_args()

    infile = Path(args.infile)
    outfile = Path(args.outfile)

    if not infile.exists():
        raise SystemExit(f"Input not found: {infile}")

    outfile.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    kept = 0
    seen = set()

    logger.info(f"Reading chunks: {infile}")
    with infile.open("r", encoding="utf-8") as f_in, outfile.open("w", encoding="utf-8") as f_out:
        for line in f_in:
            total += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            text = obj.get("text", "")
            qa = _extract_qa(text)
            if not qa:
                continue

            q, a = qa
            if len(q) < args.min_question_chars or len(a) < args.min_answer_chars:
                continue

            # de-dup by normalized q+a
            key = (q.lower(), a.lower())
            if key in seen:
                continue
            seen.add(key)

            pair = {
                # Match step3_prepare_dataset.py expected schema.
                "instruction": q,
                "input": "",
                "output": a,
                "source": f"sashwat_chroma/{obj.get('source','unknown')}",
                "text": f"Instruction: {q}\n\nResponse: {a}",
            }
            f_out.write(json.dumps(pair, ensure_ascii=False) + "\n")
            kept += 1

    logger.info(f"Chunks scanned: {total}")
    logger.info(f"Pairs kept:    {kept}")
    print("\n" + "=" * 60)
    print("  SASHWAT-ONLY PAIR GENERATION COMPLETE")
    print("=" * 60)
    print(f"  Input:   {infile}")
    print(f"  Output:  {outfile}")
    print(f"  Kept:    {kept} Q/A pairs")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
