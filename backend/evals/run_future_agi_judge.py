import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVALS_DIR = ROOT / "evals"
EXPORTER = EVALS_DIR / "export_future_agi_csv.py"


def has_ai_evaluation() -> bool:
    return importlib.util.find_spec("ai_evaluation") is not None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Future AGI judge loop preparation")
    parser.add_argument("--dataset", default=str(EVALS_DIR / "golden_cases.json"))
    parser.add_argument("--csv-out", default=str(ROOT / "future_agi_eval_dataset.csv"))
    args = parser.parse_args()

    cmd = [sys.executable, str(EXPORTER), "--input", args.dataset, "--output", args.csv_out]
    subprocess.check_call(cmd)

    print("Future AGI prep complete")
    print(f"CSV dataset: {args.csv_out}")

    if has_ai_evaluation():
        print("ai_evaluation package detected.")
        print("Next: plug CSV into your Future AGI evaluator pipeline with project credentials.")
    else:
        print("ai_evaluation package not installed.")
        print("Install when ready: pip install ai-evaluation")
        print("Then run your Future AGI judge workflow with this CSV.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
