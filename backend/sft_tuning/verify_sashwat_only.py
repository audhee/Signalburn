"""
verify_sashwat_only.py

Print source counts for the current SFT files and fail if any source is not
from Sashwat's Chroma extraction.
"""

import json
from collections import Counter
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent / "sft_data"
FILES = [
    "sft_dataset_train.jsonl",
    "sft_dataset_val.jsonl",
]


def count_sources(path: Path) -> tuple[int, Counter]:
    total = 0
    sources = Counter()
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            total += 1
            item = json.loads(line)
            source_root = item.get("source", "missing").split("/")[0]
            sources[source_root] += 1
    return total, sources


def main() -> None:
    print("\nSashwat-only source verification")
    print("=" * 40)
    all_ok = True
    for filename in FILES:
        path = DATA_DIR / filename
        total, sources = count_sources(path)
        print(f"{filename}: {total} rows | {dict(sources)}")
        if set(sources) != {"sashwat_chroma"}:
            all_ok = False

    print("=" * 40)
    if not all_ok:
        raise SystemExit("FAILED: Non-Sashwat sources found.")
    print("PASSED: all rows come from sashwat_chroma.")


if __name__ == "__main__":
    main()
