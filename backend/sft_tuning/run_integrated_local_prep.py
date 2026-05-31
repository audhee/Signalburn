"""
run_integrated_local_prep.py

Local integration runner for the three-person fine-tuning workflow.

What it does locally:
1. Vaibhav: extract Sashwat RAG chunks and build Sashwat-only SFT train/val data.
2. Anisha: refresh DPO preference data for alignment/prompt-safety behavior.
3. Integration: verify the SFT rows come only from Sashwat's Chroma database.

What it does not do locally:
- It does not train QLoRA/DPO adapters. Those need a GPU and should run on Colab.

Usage:
  python backend/sft_tuning/run_integrated_local_prep.py
"""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run_step(script_name: str, label: str) -> None:
    script_path = ROOT / script_name
    print("\n" + "=" * 70)
    print(label)
    print("=" * 70)
    result = subprocess.run([sys.executable, str(script_path)], cwd=str(ROOT.parent.parent))
    if result.returncode != 0:
        raise SystemExit(f"FAILED: {label} ({script_name})")


def main() -> None:
    print("\nArohan integrated fine-tuning local prep")
    print("Vaibhav SFT data + Amulya QLoRA handoff + Anisha DPO/prompt alignment")

    run_step("step1_extract_rag_data.py", "Step 1: Extract Sashwat RAG chunks")
    run_step("step2b_generate_sft_pairs_from_sashwat_chunks.py", "Step 2: Build Sashwat-only SFT pairs")
    run_step("step3_prepare_dataset.py", "Step 3: Prepare SFT train/val splits")
    run_step("step4b_expand_dpo_data.py", "Step 4: Build Anisha DPO preference data")
    run_step("verify_sashwat_only.py", "Step 5: Verify SFT sources are Sashwat-only")

    print("\n" + "=" * 70)
    print("LOCAL PREP COMPLETE")
    print("=" * 70)
    print("Upload this folder to Google Drive:")
    print(f"  {ROOT / 'sft_data'}")
    print("\nThen run on Colab:")
    print("  python pipeline_full_finetune.py --stage all")
    print("\nPipeline meaning:")
    print("  Vaibhav: Sashwat-only SFT dataset")
    print("  Amulya: QLoRA / PEFT training")
    print("  Anisha: DPO alignment + medical-safe prompt behavior")


if __name__ == "__main__":
    main()

