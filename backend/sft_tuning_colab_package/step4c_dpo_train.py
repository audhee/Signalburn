"""
step4c_dpo_train.py — DPO Training Script for Google Colab (Anisha's DPO Work)

Direct Preference Optimization (DPO) trains the model to prefer chosen responses
over rejected responses. This is applied ON TOP of a QLoRA-fine-tuned model.

Pipeline: Base Model → QLoRA (SFT) → DPO (preference alignment)

Usage:
    Run on Google Colab with a free T4 GPU.

Setup:
    !pip install -q unsloth
    !pip install -q --no-deps trl peft accelerate bitsandbytes
    !pip install -q datasets

    from google.colab import drive
    drive.mount('/content/drive')

    # Upload 'sft_data/' folder and 'arohan_qlora_adapter/' to your Google Drive first.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# CELL 1: Configuration — EDIT THESE PATHS FOR YOUR DRIVE
# ═══════════════════════════════════════════════════════════════════════════════

import os
import sys
import json
import torch
import logging
import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Dataset path (upload sft_data/ to your Google Drive)
DATASET_DIR      = "/content/drive/MyDrive/arohan_sft_data"
DPO_TRAIN_FILE   = os.path.join(DATASET_DIR, "dpo_dataset_train.jsonl")
DPO_VAL_FILE     = os.path.join(DATASET_DIR, "dpo_dataset_val.jsonl")

# QLoRA adapter from step4 (the SFT fine-tuned adapter to start DPO from)
QLORA_ADAPTER_PATH = "/content/drive/MyDrive/arohan_qlora_adapter/experiment_medium"

# Output path for DPO-trained adapter
OUTPUT_DIR = "/content/drive/MyDrive/arohan_dpo_adapter"

# Model
BASE_MODEL = "unsloth/llama-3-8b-Instruct-bnb-4bit"
MAX_SEQ_LENGTH = 2048
DTYPE = None
LOAD_IN_4BIT = True

# DPO hyperparameters
BETA = 0.1          # DPO temperature — lower = more emphasis on avoiding rejected responses
LEARNING_RATE = 5e-6  # Very low for preference alignment (SFT was ~2e-4)
NUM_EPOCHS = 2
BATCH_SIZE = 2
GRAD_ACCUM = 4


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 2: Load Base Model + QLoRA Adapter
# ═══════════════════════════════════════════════════════════════════════════════
# DPO is applied ON TOP of the QLoRA fine-tuned model, not from scratch.

def load_pretrained_qlora():
    """Load the base 4-bit model with the QLoRA adapter from step4."""
    from unsloth import FastLanguageModel
    from peft import PeftModel

    logger.info(f"Loading base model: {BASE_MODEL}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=DTYPE,
        load_in_4bit=LOAD_IN_4BIT,
    )

    logger.info(f"Loading QLoRA adapter from: {QLORA_ADAPTER_PATH}")
    model = PeftModel.from_pretrained(model, QLORA_ADAPTER_PATH)
    logger.info("QLoRA adapter loaded successfully! Base is SFT-tuned.")

    vram_gb = torch.cuda.memory_allocated() / 1024**3
    logger.info(f"Model + adapter loaded! VRAM: {vram_gb:.2f} GB")

    # Ensure the model is in training mode for DPO
    model.train()
    return model, tokenizer


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 3: Load DPO Dataset
# ═══════════════════════════════════════════════════════════════════════════════
# DPO dataset has: prompt, chosen, rejected
# The DPOTrainer expects these fields.

def load_dpo_datasets():
    """Load DPO preference pairs."""
    from datasets import load_dataset

    logger.info(f"Loading DPO training data from: {DPO_TRAIN_FILE}")
    train_dataset = load_dataset("json", data_files=DPO_TRAIN_FILE, split="train")
    logger.info(f"  Training DPO pairs: {len(train_dataset)}")

    val_dataset = None
    if os.path.exists(DPO_VAL_FILE):
        val_dataset = load_dataset("json", data_files=DPO_VAL_FILE, split="train")
        logger.info(f"  Validation DPO pairs: {len(val_dataset)}")

    # Show a sample
    sample = train_dataset[0]
    logger.info(f"\n  Sample prompt:    {sample['prompt'][:80]}...")
    logger.info(f"  Sample chosen:    {sample['chosen'][:80]}...")
    logger.info(f"  Sample rejected:  {sample['rejected'][:80]}...")

    return train_dataset, val_dataset


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 4: Build DPO Training Function
# ═══════════════════════════════════════════════════════════════════════════════
# DPO loss function:
#   L = -E[ log σ(β * (log π_θ(y_w|x) - log π_θ(y_l|x) - (log π_ref(y_w|x) - log π_ref(y_l|x)))) ]
# Where:
#   y_w = chosen response, y_l = rejected response
#   π_θ = policy model, π_ref = reference model (frozen)
#   β = temperature parameter controlling how much to penalize rejected responses

# In TRL's DPOTrainer, the reference model is automatically created by copying
# the policy model and freezing its weights.

def run_dpo_training(model, tokenizer, train_dataset, val_dataset):
    """Run DPO training using TRL's DPOTrainer."""
    from trl import DPOTrainer, DPOConfig

    logger.info("=" * 60)
    logger.info("Configuring DPO Training")
    logger.info("=" * 60)
    logger.info(f"  Beta (DPO temperature):   {BETA}")
    logger.info(f"  Learning rate:            {LEARNING_RATE}")
    logger.info(f"  Epochs:                   {NUM_EPOCHS}")
    logger.info(f"  Batch size:               {BATCH_SIZE} (effective: {BATCH_SIZE * GRAD_ACCUM})")

    # DPO uses a specific formatting function for the chat template
    def formatting_func(example):
        """Format DPO examples for Llama 3 chat template."""
        # The DPOTrainer expects 'prompt', 'chosen', 'rejected' columns
        # and will apply the tokenizer with the chat template
        return example

    training_args = DPOConfig(
        output_dir=os.path.join(OUTPUT_DIR, "checkpoints"),

        # DPO training hyperparameters
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        num_train_epochs=NUM_EPOCHS,
        learning_rate=LEARNING_RATE,
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        weight_decay=0.01,

        # Precision — force fp16 (bf16 causes grad_scaler issues on T4 with DPOTrainer)
        fp16=True,
        bf16=False,

        # Logging
        logging_steps=10,
        logging_first_step=True,
        report_to="none",

        # Evaluation
        eval_strategy="epoch" if val_dataset else "no",

        # Saving
        save_strategy="epoch",
        save_total_limit=2,

        # Performance
        optim="adamw_8bit",
        seed=42,

        # Gradient checkpointing for memory savings
        gradient_checkpointing=True,
    )

    # The DPOTrainer automatically creates a reference model (frozen copy of policy)
    trainer = DPOTrainer(
        model=model,
        ref_model=None,  # Auto-created from policy with frozen weights
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        args=training_args,
        beta=BETA,
        max_prompt_length=512,
        max_length=MAX_SEQ_LENGTH,
    )

    logger.info("\n" + "=" * 60)
    logger.info("Starting DPO training...")
    logger.info("=" * 60)

    trainer_stats = trainer.train()

    logger.info("\n" + "=" * 60)
    logger.info("DPO TRAINING COMPLETE!")
    logger.info("=" * 60)
    logger.info(f"  Training loss:  {trainer_stats.training_loss:.4f}")
    logger.info(f"  Training time:  {trainer_stats.metrics.get('train_runtime', 0):.0f}s")

    return trainer, trainer_stats


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 5: Save DPO-trained Adapter
# ═══════════════════════════════════════════════════════════════════════════════

def save_dpo_adapter(model, tokenizer, train_dataset, val_dataset):
    """Save the DPO-trained adapter."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    logger.info(f"Saving DPO adapter to: {OUTPUT_DIR}")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    # Save DPO training config
    config = {
        "base_model": BASE_MODEL,
        "qlora_adapter_source": QLORA_ADAPTER_PATH,
        "dpo_hyperparameters": {
            "beta": BETA,
            "learning_rate": LEARNING_RATE,
            "num_epochs": NUM_EPOCHS,
            "batch_size": BATCH_SIZE,
            "gradient_accumulation": GRAD_ACCUM,
        },
        "dataset_sizes": {
            "dpo_train_pairs": len(train_dataset),
            "dpo_val_pairs": len(val_dataset) if val_dataset else 0,
        }
    }

    with open(os.path.join(OUTPUT_DIR, "dpo_config.json"), "w") as f:
        json.dump(config, f, indent=2)

    logger.info(f"DPO adapter saved! Size: ~50 MB")
    logger.info(f"Config saved to: {OUTPUT_DIR}/dpo_config.json")


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 6: Main
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "#" * 60)
    print("#  DPO Training — Arohan Medical First Aid")
    print("#  Direct Preference Optimization via TRL")
    print("#" * 60 + "\n")

    if not torch.cuda.is_available():
        logger.error("CUDA not available! This script requires a GPU (Google Colab T4 or better).")
        sys.exit(1)

    logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
    logger.info(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB\n")

    # Load QLoRA-pretrained model
    model, tokenizer = load_pretrained_qlora()

    # Load DPO dataset
    train_dataset, val_dataset = load_dpo_datasets()

    # Run DPO training
    trainer, trainer_stats = run_dpo_training(model, tokenizer, train_dataset, val_dataset)

    # Save adapter
    save_dpo_adapter(model, tokenizer, train_dataset, val_dataset)

    print("\n" + "#" * 60)
    print("#  DPO TRAINING COMPLETE!")
    print("#" * 60)
    print(f"#  Adapter saved to: {OUTPUT_DIR}/")
    print("#")
    print("#  Next steps:")
    print("#  1. Run inference with the DPO + QLoRA adapter:")
    print("#     python inference_qlora.py --adapter ./arohan_dpo_adapter")
    print("#  2. Compare with QLoRA-only vs Groq:")
    print("#     python step5_evaluate_comprehensive.py")
    print("#" * 60 + "\n")
