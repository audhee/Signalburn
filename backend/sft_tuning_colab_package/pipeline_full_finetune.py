"""
pipeline_full_finetune.py — Full Fine-Tuning Pipeline: SFT -> QLoRA -> DPO -> Eval

This script orchestrates the entire Arohan LLM fine-tuning pipeline on Google Colab.

Pipeline Flow:
  1. Dataset Preparation (step2 + step3) - already done, just upload sft_data/
  2. QLoRA Fine-Tuning (step4_qlora_train.py) - Amulya's PEFT
  3. DPO Preference Alignment (step4c_dpo_train.py) - Anisha's alignment
  4. Comprehensive Evaluation (step5_evaluate_comprehensive.py) - Vaibhav's eval

Usage on Colab:
    !pip install -q unsloth
    !pip install -q --no-deps trl peft accelerate bitsandbytes
    !pip install -q datasets

    from google.colab import drive
    drive.mount('/content/drive')

    # Upload the entire sft_data/ folder to /content/drive/MyDrive/arohan_sft_data/
    # Then run:
    python pipeline_full_finetune.py --stage all

Stages:
    --stage sft       : Run QLoRA training (SFT) only
    --stage dpo       : Run DPO training on top of QLoRA adapter
    --stage eval      : Run evaluation comparing all models
    --stage all       : Run full pipeline (SFT -> DPO -> Eval)
"""

import os
import sys
import json
import time
import torch
import logging
import argparse
import subprocess

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# --- Configuration -----------------------------------------------------------
DRIVE_DIR       = "/content/drive/MyDrive/arohan_sft_data"
DATASET_DIR     = DRIVE_DIR
QLORA_OUTPUT    = "/content/drive/MyDrive/arohan_qlora_adapter"
DPO_OUTPUT      = "/content/drive/MyDrive/arohan_dpo_adapter"
EVAL_OUTPUT     = "/content/drive/MyDrive/arohan_eval_results"

PIPELINE_LOG    = "/content/drive/MyDrive/arohan_pipeline_log.json"

# --- Utility -----------------------------------------------------------------

def log_step(step_name: str, status: str, details: dict = None):
    """Log a pipeline step to the pipeline log file."""
    entry = {
        "step": step_name,
        "status": status,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "details": details or {},
    }

    log_path = PIPELINE_LOG
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    log_data = []
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            log_data = json.load(f)

    log_data.append(entry)

    with open(log_path, "w") as f:
        json.dump(log_data, f, indent=2)

    logger.info(f"[{step_name}] {status}")


def run_script(script_path: str, description: str, extra_args: list = None, timeout_minutes: int = 30):
    """Run a Python script and log the result."""
    logger.info(f"=" * 60)
    logger.info(f"Running: {description}")
    logger.info(f"Script:  {script_path}")
    if extra_args:
        logger.info(f"Args:    {' '.join(extra_args)}")
    logger.info(f"=" * 60)

    cmd = [sys.executable, script_path] + (extra_args or [])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_minutes * 60,
        )

        if result.returncode == 0:
            log_step(description, "SUCCESS", {
                "script": script_path,
                "stdout_len": len(result.stdout),
                "stderr_len": len(result.stderr),
            })
            logger.info(f"[DONE] {description} completed successfully.")
            return True
        else:
            log_step(description, "FAILED", {
                "script": script_path,
                "returncode": result.returncode,
                "stderr": result.stderr[-500:],
            })
            logger.error(f"[FAILED] {description} failed with code {result.returncode}")
            logger.error(f"stderr: {result.stderr[-500:]}")
            return False

    except subprocess.TimeoutExpired:
        log_step(description, "TIMEOUT", {
            "script": script_path,
            "timeout_minutes": timeout_minutes,
        })
        logger.error(f"[TIMEOUT] {description} exceeded {timeout_minutes} minutes.")
        return False

    except Exception as e:
        log_step(description, "ERROR", {
            "script": script_path,
            "error": str(e),
        })
        logger.error(f"[ERROR] {description}: {e}")
        return False


# --- Stage 1: Verify Dataset -------------------------------------------------

def verify_dataset():
    """Verify all dataset files exist and have content."""
    required_files = [
        "sft_dataset_train.jsonl",
        "sft_dataset_val.jsonl",
        "dpo_dataset_train.jsonl",
        "dpo_dataset_val.jsonl",
    ]

    missing = []
    for f in required_files:
        path = os.path.join(DATASET_DIR, f)
        if not os.path.exists(path):
            missing.append(f)

    if missing:
        logger.error(f"Missing dataset files: {missing}")
        logger.error(f"Upload sft_data/ folder to {DATASET_DIR}")
        return False

    # Check sizes
    sizes = {}
    for f in required_files:
        path = os.path.join(DATASET_DIR, f)
        sizes[f] = os.path.getsize(path)

    logger.info("Dataset verified:")
    for name, size in sizes.items():
        logger.info(f"  {name}: {size:,} bytes")

    # SFT rows must come from Sashwat's Chroma extraction for this integrated path.
    source_counts = {}
    for f in ["sft_dataset_train.jsonl", "sft_dataset_val.jsonl"]:
        path = os.path.join(DATASET_DIR, f)
        with open(path, "r", encoding="utf-8") as dataset_file:
            for line in dataset_file:
                if not line.strip():
                    continue
                item = json.loads(line)
                source_root = item.get("source", "missing").split("/")[0]
                source_counts[source_root] = source_counts.get(source_root, 0) + 1

    if set(source_counts) != {"sashwat_chroma"}:
        logger.error(f"SFT dataset contains non-Sashwat sources: {source_counts}")
        return False

    logger.info(f"Sashwat-only SFT source check passed: {source_counts}")

    log_step("verify_dataset", "OK", {"files": sizes, "sft_sources": source_counts})
    return True


# --- Stage 2: QLoRA Training (SFT) -------------------------------------------

def run_qlora_training():
    """Run QLoRA SFT training."""
    script_path = os.path.join(os.path.dirname(__file__), "step4_qlora_train.py")
    if not os.path.exists(script_path):
        logger.error(f"QLoRA training script not found: {script_path}")
        return False

    return run_script(script_path, "QLoRA SFT Training", timeout_minutes=30)


# --- Stage 3: DPO Training ---------------------------------------------------

def run_dpo_training():
    """Run DPO preference alignment on top of QLoRA adapter."""
    # Check that QLoRA adapter exists
    if not os.path.exists(QLORA_OUTPUT):
        logger.warning(f"QLoRA adapter not found at {QLORA_OUTPUT}")
        logger.warning("Did you run the QLoRA stage first?")
        return False

    # Check if DPO adapter was already trained
    if os.path.exists(DPO_OUTPUT):
        logger.info(f"DPO adapter already exists at {DPO_OUTPUT}")
        logger.info("Skipping DPO training. Delete DPO adapter to re-train.")
        log_step("DPO Training", "SKIPPED (already exists)", {"path": DPO_OUTPUT})
        return True

    script_path = os.path.join(os.path.dirname(__file__), "step4c_dpo_train.py")
    if not os.path.exists(script_path):
        logger.error(f"DPO training script not found: {script_path}")
        return False

    return run_script(script_path, "DPO Preference Alignment", timeout_minutes=20)


# --- Stage 4: Comprehensive Evaluation ---------------------------------------

def run_evaluation():
    """Run comprehensive evaluation comparing all models."""
    script_path = os.path.join(os.path.dirname(__file__), "step5_evaluate_comprehensive.py")
    if not os.path.exists(script_path):
        logger.error(f"Evaluation script not found: {script_path}")
        return False

    # Build args to pass trained adapters if they exist
    extra_args = []
    if os.path.exists(QLORA_OUTPUT):
        # Find the actual experiment subfolder
        exp_dirs = sorted([d for d in os.listdir(QLORA_OUTPUT) if d.startswith("experiment_")])
        if exp_dirs:
            latest_exp = os.path.join(QLORA_OUTPUT, exp_dirs[0])
            extra_args.extend(["--qlora-adapter", latest_exp])
    if os.path.exists(DPO_OUTPUT):
        extra_args.extend(["--dpo-adapter", DPO_OUTPUT])

    # Also try Groq
    extra_args.append("--groq")

    return run_script(script_path, "Comprehensive Evaluation", extra_args=extra_args, timeout_minutes=45)


# --- Main Pipeline -----------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Arohan Full Fine-Tuning Pipeline")
    parser.add_argument("--stage", type=str, default="all",
                       choices=["verify", "sft", "dpo", "eval", "all"],
                       help="Pipeline stage to run")
    parser.add_argument("--skip-verify", action="store_true",
                       help="Skip dataset verification")
    args = parser.parse_args()

    print("\n" + "#" * 70)
    print("#  Arohan Full Fine-Tuning Pipeline")
    print("#  SFT (QLoRA) -> DPO -> Evaluation")
    print("#" * 70 + "\n")

    if not torch.cuda.is_available():
        logger.error("CUDA not available! This pipeline requires a GPU (Colab T4+).")
        sys.exit(1)

    logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
    logger.info(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    logger.info(f"Dataset: {DATASET_DIR}")
    logger.info(f"Pipeline log: {PIPELINE_LOG}\n")

    # Track overall status
    overall_status = {"verified": False, "sft_done": False, "dpo_done": False, "eval_done": False}

    # Stage: Verify Dataset
    if args.stage in ["verify", "all"]:
        if not args.skip_verify:
            overall_status["verified"] = verify_dataset()
            if not overall_status["verified"] and args.stage != "all":
                sys.exit(1)
            if not overall_status["verified"]:
                logger.warning("Dataset verification failed. Continuing anyway...")

    # Stage: QLoRA (SFT)
    if args.stage in ["sft", "all"]:
        overall_status["sft_done"] = run_qlora_training()

    # Stage: DPO
    if args.stage in ["dpo", "all"]:
        overall_status["dpo_done"] = run_dpo_training()

    # Stage: Evaluation
    if args.stage in ["eval", "all"]:
        overall_status["eval_done"] = run_evaluation()

    # Final Summary
    print("\n" + "#" * 70)
    print("#  PIPELINE COMPLETE")
    print("#" * 70)
    print(f"  Dataset verified:  {overall_status['verified']}")
    print(f"  QLoRA (SFT):       {overall_status['sft_done']}")
    print(f"  DPO:               {overall_status['dpo_done']}")
    print(f"  Evaluation:        {overall_status['eval_done']}")
    print()
    print("  Output locations:")
    print(f"    QLoRA adapter:   {QLORA_OUTPUT}/")
    print(f"    DPO adapter:     {DPO_OUTPUT}/")
    print(f"    Eval results:    {EVAL_OUTPUT}/")
    print(f"    Pipeline log:    {PIPELINE_LOG}")
    print()

    # Count successes
    successes = sum(1 for v in overall_status.values() if v is True)
    attempted = sum(1 for v in overall_status.values() if v is not None)

    if successes == attempted:
        print("  Status: ALL STEPS PASSED")
    else:
        print(f"  Status: {successes}/{attempted} steps passed")
    print("#" * 70 + "\n")


if __name__ == "__main__":
    main()
