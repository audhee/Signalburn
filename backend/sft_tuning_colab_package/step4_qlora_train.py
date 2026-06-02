"""
step4_qlora_train.py — QLoRA Training Script for Google Colab (Amulya's PEFT work)
Uses Unsloth for fast 4-bit QLoRA fine-tuning on free T4 GPU.

Run this on Google Colab. Upload the sft_data/ folder to your Google Drive first.

Usage:
    python step4_qlora_train.py       # Runs on Colab
"""

# ═══════════════════════════════════════════════════════════════════════════════
# CELL 1: Install Dependencies (Run in Colab)
# ═══════════════════════════════════════════════════════════════════════════════
"""
# Paste this in the first Colab cell:

!pip install -q unsloth
!pip install -q --no-deps trl peft accelerate bitsandbytes
!pip install -q datasets

from google.colab import drive
drive.mount('/content/drive')
"""

import os
import sys
import json
import torch
import logging
import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CELL 2: Configuration — EDIT THESE PATHS FOR YOUR DRIVE
# ═══════════════════════════════════════════════════════════════════════════════

# Dataset path (upload sft_data/ to your Google Drive)
DATASET_DIR = "/content/drive/MyDrive/arohan_sft_data"
TRAIN_FILE = os.path.join(DATASET_DIR, "sft_dataset_train.jsonl")
VAL_FILE   = os.path.join(DATASET_DIR, "sft_dataset_val.jsonl")

# Output paths
OUTPUT_DIR    = "/content/drive/MyDrive/arohan_qlora_adapter"
EXPERIMENTS_FILE = os.path.join(OUTPUT_DIR, "hyperparameter_experiments.json")

# Model
BASE_MODEL = "unsloth/llama-3-8b-Instruct-bnb-4bit"
MAX_SEQ_LENGTH = 2048
DTYPE = None          # Auto-detect
LOAD_IN_4BIT = True   # Required for free T4 (16GB VRAM)

# ═══════════════════════════════════════════════════════════════════════════════
# CELL 3: Hyperparameter Grid — Amulya experiments with these
# ═══════════════════════════════════════════════════════════════════════════════

# You can run each combination and record results in the comparison table.
# Start with "medium" (r=16, alpha=32, epochs=3) for best balance.
EXPERIMENTS = {
    "baseline": {
        "r": 8,
        "lora_alpha": 16,
        "lora_dropout": 0.0,
        "num_epochs": 1,
        "learning_rate": 2e-4,
        "description": "Low rank, 1 epoch — quick baseline"
    },
    "medium": {
        "r": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.0,
        "num_epochs": 3,
        "learning_rate": 2e-4,
        "description": "Medium rank, 3 epochs — recommended first try"
    },
    "high": {
        "r": 32,
        "lora_alpha": 64,
        "lora_dropout": 0.05,
        "num_epochs": 5,
        "learning_rate": 1e-4,
        "description": "High rank, 5 epochs — maximum capacity"
    }
}

# Which experiment to run. Change this to "baseline", "medium", or "high"
ACTIVE_EXPERIMENT = "medium"


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 4: Load Base Model with 4-bit Quantization
# ═══════════════════════════════════════════════════════════════════════════════

def load_base_model():
    """Load Llama 3 8B with 4-bit quantization via Unsloth."""
    from unsloth import FastLanguageModel

    logger.info(f"Loading base model: {BASE_MODEL}")
    logger.info(f"  Max sequence length: {MAX_SEQ_LENGTH}")
    logger.info(f"  4-bit quantized: {LOAD_IN_4BIT}")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=DTYPE,
        load_in_4bit=LOAD_IN_4BIT,
    )

    vram_gb = torch.cuda.memory_allocated() / 1024**3
    logger.info(f"Model loaded! VRAM usage: {vram_gb:.2f} GB")
    return model, tokenizer


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 5: Add LoRA Adapters (QLoRA — training only the adapters)
# ═══════════════════════════════════════════════════════════════════════════════

def add_lora_adapters(model, exp_config):
    """Attach LoRA adapters to the quantized model.
    
    Key QLoRA concept: The base model stays in 4-bit. Only the LoRA
    adapter weights (in fp16/bf16) are updated during training.
    This keeps memory usage ~50x lower than full fine-tuning.
    """
    from unsloth import FastLanguageModel

    logger.info(f"Adding LoRA adapters (r={exp_config['r']}, alpha={exp_config['lora_alpha']})")
    logger.info(f"  Trainable parameters: ~{exp_config['r'] * len(TARGET_MODULES) * 2 * 4096 / 1e6:.1f}M out of 8B (0.08%)")

    model = FastLanguageModel.get_peft_model(
        model,
        r=exp_config["r"],
        target_modules=TARGET_MODULES,
        lora_alpha=exp_config["lora_alpha"],
        lora_dropout=exp_config["lora_dropout"],
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    model.print_trainable_parameters()
    return model


# Target modules — standard for Llama 3
TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",  # Attention
    "gate_proj", "up_proj", "down_proj",       # MLP
]


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 6: Load Dataset
# ═══════════════════════════════════════════════════════════════════════════════

def load_datasets():
    """Load train/val JSONL datasets.
    
    The dataset already has a 'text' field formatted as Llama 3 chat template
    (with <|begin_of_text|>, <|start_header_id|>, etc.) from step3.
    """
    from datasets import load_dataset

    logger.info(f"Loading training data from: {TRAIN_FILE}")
    train_dataset = load_dataset("json", data_files=TRAIN_FILE, split="train")
    logger.info(f"  Training samples: {len(train_dataset)}")

    val_dataset = None
    if os.path.exists(VAL_FILE):
        val_dataset = load_dataset("json", data_files=VAL_FILE, split="train")
        logger.info(f"  Validation samples: {len(val_dataset)}")

    logger.info(f"  Sample text (first 200 chars): {train_dataset[0]['text'][:200]}")
    return train_dataset, val_dataset


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 7: Train — SFTTrainer with QLoRA
# ═══════════════════════════════════════════════════════════════════════════════

def train(model, tokenizer, train_dataset, val_dataset, exp_config):
    """Run QLoRA training using SFTTrainer from TRL.
    
    QLoRA = Quantized Low-Rank Adaptation:
    - Base model: 4-bit NormalFloat (NF4)
    - Adapters: bfloat16 (on supported GPUs) or float16
    - Only adapter gradients are computed — base model frozen
    """
    from trl import SFTTrainer
    from transformers import TrainingArguments

    exp_name = ACTIVE_EXPERIMENT
    exp = exp_config

    # Effective batch size = per_device * gradient_accumulation
    # For 1,040 samples with batch_size=2 and grad_accum=4 → effective=8
    # Steps per epoch = 1040/8 = 130. 3 epochs = 390 steps. ~10 min on T4.
    BATCH_SIZE = 2
    GRAD_ACCUM = 4
    EFFECTIVE_BATCH = BATCH_SIZE * GRAD_ACCUM
    TOTAL_STEPS = (len(train_dataset) // EFFECTIVE_BATCH) * exp["num_epochs"]

    logger.info(f"  Effective batch size: {EFFECTIVE_BATCH}")
    logger.info(f"  Total steps: {TOTAL_STEPS}")
    logger.info(f"  Learning rate: {exp['learning_rate']}")
    logger.info(f"  Epochs: {exp['num_epochs']}")

    output_subdir = os.path.join(OUTPUT_DIR, f"experiment_{exp_name}")

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            # Output
            output_dir=output_subdir,

            # QLoRA training hyperparameters
            num_train_epochs=exp["num_epochs"],
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRAD_ACCUM,
            learning_rate=exp["learning_rate"],
            lr_scheduler_type="cosine",
            warmup_ratio=0.03,
            weight_decay=0.01,

            # Precision
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),

            # Logging
            logging_steps=10,
            logging_first_step=True,
            report_to="none",

            # Evaluation
            eval_strategy="epoch",
            eval_steps=None,

            # Save checkpoints
            save_strategy="epoch",
            save_steps=None,
            save_total_limit=2,

            # Optimizer
            optim="adamw_8bit",
            seed=42,
        ),
    )

    logger.info("=" * 60)
    logger.info("Starting QLoRA training...")
    logger.info("=" * 60)

    trainer_stats = trainer.train()

    # Summarize
    logger.info("=" * 60)
    logger.info("TRAINING COMPLETE!")
    logger.info("=" * 60)
    logger.info(f"  Experiment:       {exp_name} ({exp['description']})")
    logger.info(f"  Training loss:    {trainer_stats.training_loss:.4f}")
    logger.info(f"  Training time:    {trainer_stats.metrics.get('train_runtime', 0):.0f}s")
    logger.info(f"  Samples/second:   {trainer_stats.metrics.get('train_samples_per_second', 0):.2f}")

    # Save adapter
    os.makedirs(output_subdir, exist_ok=True)
    model.save_pretrained(output_subdir)
    tokenizer.save_pretrained(output_subdir)
    logger.info(f"Adapter saved to: {output_subdir}")

    # Log experiment results
    _log_experiment(exp_name, exp, trainer_stats, output_subdir)

    return trainer_stats


def _log_experiment(exp_name, exp_config, trainer_stats, output_dir):
    """Append experiment result to the hyperparameter comparison file."""
    result = {
        "experiment": exp_name,
        "description": exp_config["description"],
        "hyperparameters": {
            "r": exp_config["r"],
            "lora_alpha": exp_config["lora_alpha"],
            "lora_dropout": exp_config["lora_dropout"],
            "num_epochs": exp_config["num_epochs"],
            "learning_rate": exp_config["learning_rate"],
        },
        "results": {
            "training_loss": trainer_stats.training_loss,
            "train_runtime_seconds": trainer_stats.metrics.get("train_runtime", 0),
            "train_samples_per_second": trainer_stats.metrics.get("train_samples_per_second", 0),
            "gpu_vram_gb": torch.cuda.memory_allocated() / 1024**3,
        },
        "timestamp": datetime.datetime.now().isoformat(),
    }

    os.makedirs(os.path.dirname(EXPERIMENTS_FILE), exist_ok=True)
    experiments = []
    if os.path.exists(EXPERIMENTS_FILE):
        with open(EXPERIMENTS_FILE, "r") as f:
            experiments = json.load(f)
    experiments.append(result)

    with open(EXPERIMENTS_FILE, "w") as f:
        json.dump(experiments, f, indent=2)

    logger.info(f"Experiment logged to: {EXPERIMENTS_FILE}")


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 8: Quick Inference Test (After Training)
# ═══════════════════════════════════════════════════════════════════════════════

def test_inference(model, tokenizer):
    """Run a quick test to verify the trained model produces good responses."""
    from unsloth import FastLanguageModel

    FastLanguageModel.for_inference(model)

    test_queries = [
        "What should I do if my nose is bleeding?",
        "Someone fainted and is not responding. What first aid should I give?",
        "How to treat a minor burn from hot oil?",
    ]

    logger.info("\n" + "=" * 50)
    logger.info("INFERENCE TEST")
    logger.info("=" * 50)

    for query in test_queries:
        messages = [
            {"role": "system", "content": "You are Arohan, a medical first aid assistant for elderly Indians. Provide clear, numbered first aid steps using simple words."},
            {"role": "user", "content": query},
        ]

        prompt = tokenizer.apply_chat_template(messages, tokenize=False) + "<|start_header_id|>assistant<|end_header_id|>\n\n"
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

        outputs = model.generate(
            **inputs,
            max_new_tokens=300,
            temperature=0.1,
            do_sample=True,
            top_p=0.9,
        )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract assistant response
        if "assistant" in response:
            response = response.split("assistant")[-1].strip()

        logger.info(f"\nQ: {query}")
        logger.info(f"A: {response[:400]}")
        logger.info("-" * 50)


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 9: Merge Adapter for Deployment
# ═══════════════════════════════════════════════════════════════════════════════

def merge_adapter(model, tokenizer, exp_config):
    """Merge the LoRA adapter into the base model and save as a single model.
    
    This is optional — for deployment you can either:
    A) Keep adapter separate (load base + adapter at inference) — 50MB
    B) Merge adapter into base (larger file but no adapter loading needed) — 16GB
    """
    logger.info("Merging LoRA adapter into base model (this may take a few minutes)...")

    merged_dir = os.path.join(OUTPUT_DIR, f"experiment_{ACTIVE_EXPERIMENT}_merged")
    os.makedirs(merged_dir, exist_ok=True)

    from unsloth import FastLanguageModel
    merged_model = model.merge_and_unload()
    merged_model.save_pretrained(merged_dir)
    tokenizer.save_pretrained(merged_dir)

    logger.info(f"Merged model saved to: {merged_dir}")
    logger.info(f"  Size: {sum(os.path.getsize(os.path.join(merged_dir, f)) for f in os.listdir(merged_dir) if os.path.isfile(os.path.join(merged_dir, f))) / 1024**3:.2f} GB")


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 10: Main — Run All Steps
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "#" * 60)
    print("#  QLoRA Training — Arohan Medical First Aid")
    print("#  Amulya's PEFT (Parameter-Efficient Fine-Tuning)")
    print("#" * 60 + "\n")

    # Validate CUDA
    if not torch.cuda.is_available():
        logger.error("CUDA not available! This script requires a GPU (Google Colab T4 or better).")
        logger.error("Upload sft_data/ to Google Drive and run this on Colab.")
        sys.exit(1)

    logger.info(f"Active experiment: {ACTIVE_EXPERIMENT}")
    logger.info(f"Configuration: {EXPERIMENTS[ACTIVE_EXPERIMENT]['description']}")
    logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
    logger.info(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB\n")

    # Step 4: Load model
    model, tokenizer = load_base_model()

    # Step 5: Add LoRA adapters
    exp_config = EXPERIMENTS[ACTIVE_EXPERIMENT]
    model = add_lora_adapters(model, exp_config)

    # Step 6: Load dataset
    train_dataset, val_dataset = load_datasets()

    # Step 7: Train
    trainer_stats = train(model, tokenizer, train_dataset, val_dataset, exp_config)

    # Step 8: Test inference
    test_inference(model, tokenizer)

    # Step 9: Save merged model (optional — uncomment to run)
    # merge_adapter(model, tokenizer, exp_config)

    print("\n" + "#" * 60)
    print("#  QLoRA TRAINING COMPLETE!")
    print("#" * 60)
    print(f"#  Adapter saved to: {OUTPUT_DIR}/experiment_{ACTIVE_EXPERIMENT}/")
    print(f"#")
    print(f"#  Next steps:")
    print(f"#  1. Run more experiments (change ACTIVE_EXPERIMENT)")
    print(f"#  2. Compare results in hyperparameter_experiments.json")
    print(f"#  3. Test with inference_qlora.py locally")
    print(f"#  4. Upload adapter to Hugging Face Hub")
    print("#" * 60 + "\n")
