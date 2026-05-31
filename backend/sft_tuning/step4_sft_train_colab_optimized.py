"""
step4_sft_train_colab_optimized.py — Optimized SFT Training Script for Google Colab
Removes slow steps (HuggingFace login, GGUF export) to focus on training.
Run this on Google Colab with a free T4 GPU.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# CELL 1: Install Dependencies & Setup
# ═══════════════════════════════════════════════════════════════════════════════
"""
# Run this in the first Colab cell:

!pip install -q unsloth
!pip install -q --no-deps trl peft accelerate bitsandbytes
!pip install -q datasets

# Mount Google Drive (to load dataset and save model)
from google.colab import drive
drive.mount('/content/drive')
"""

# ═══════════════════════════════════════════════════════════════════════════════
# CELL 2: Load Model
# ═══════════════════════════════════════════════════════════════════════════════

import os
import torch
from unsloth import FastLanguageModel

# Configuration
MAX_SEQ_LENGTH = 2048
DTYPE = None  # Auto-detect (float16 for T4)
LOAD_IN_4BIT = True  # Required for free Colab T4 (16GB VRAM)

# Dataset path on Google Drive
DATASET_DIR = "/content/drive/MyDrive/arohan_sft_data"
TRAIN_FILE = os.path.join(DATASET_DIR, "sft_dataset_train.jsonl")
VAL_FILE   = os.path.join(DATASET_DIR, "sft_dataset_val.jsonl")
OUTPUT_DIR = "/content/drive/MyDrive/arohan_sft_model"

print("Loading Llama 3 8B Instruct (4-bit quantized)...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/llama-3-8b-Instruct-bnb-4bit",
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=DTYPE,
    load_in_4bit=LOAD_IN_4BIT,
)
print(f"✅ Model loaded! VRAM usage: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 3: Add LoRA Adapters
# ═══════════════════════════════════════════════════════════════════════════════

print("Adding LoRA adapters for parameter-efficient training...")
model = FastLanguageModel.get_peft_model(
    model,
    r=16,                       # LoRA rank — 16 is a good balance
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",  # Attention layers
        "gate_proj", "up_proj", "down_proj",       # MLP layers
    ],
    lora_alpha=16,              # Scaling factor
    lora_dropout=0,             # 0 is recommended by Unsloth
    bias="none",
    use_gradient_checkpointing="unsloth",  # 30% less VRAM
    random_state=42,
)

# Print trainable parameter stats
model.print_trainable_parameters()
# Expected: ~0.08% of total parameters are trainable


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 4: Load & Prepare Dataset
# ═══════════════════════════════════════════════════════════════════════════════

from datasets import load_dataset

print(f"Loading training dataset from: {TRAIN_FILE}")

# Load JSONL dataset
train_dataset = load_dataset(
    "json",
    data_files=TRAIN_FILE,
    split="train"
)

# The 'text' field already contains the Llama 3 formatted chat template
# from step3_prepare_dataset.py
print(f"✅ Training dataset: {len(train_dataset)} samples")
print(f"\nSample entry (first 300 chars):")
print(train_dataset[0]["text"][:300])

# Load validation set if it exists
val_dataset = None
if os.path.exists(VAL_FILE):
    val_dataset = load_dataset(
        "json",
        data_files=VAL_FILE,
        split="train"
    )
    print(f"✅ Validation dataset: {len(val_dataset)} samples")


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 5: Configure & Start Training (Optimized for Small Dataset)
# ═══════════════════════════════════════════════════════════════════════════════

from trl import SFTTrainer
from transformers import TrainingArguments

print("Configuring SFT trainer...")

# Optimized parameters for your small dataset (83 samples)
NUM_EPOCHS = 3
BATCH_SIZE = 1  # Reduced to save VRAM
GRAD_ACCUM = 8  # Increased to compensate for smaller batch
EFFECTIVE_BATCH = BATCH_SIZE * GRAD_ACCUM  # = 8
TOTAL_STEPS = (len(train_dataset) // EFFECTIVE_BATCH) * NUM_EPOCHS

print(f"  Effective batch size: {EFFECTIVE_BATCH}")
print(f"  Total training steps: {TOTAL_STEPS}")
print(f"  Epochs: {NUM_EPOCHS}")

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LENGTH,
    dataset_num_proc=2,
    packing=False,  # Can set True for shorter sequences to speed up
    args=TrainingArguments(
        # Output
        output_dir="./sft_checkpoints",

        # Training hyperparameters
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_steps=5,  # Reduced for small dataset
        weight_decay=0.01,

        # Precision
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),

        # Logging - increased steps since dataset is small
        logging_steps=1,  # Log every step for small dataset
        logging_first_step=True,

        # Evaluation
        eval_strategy="epoch",  # Evaluate at end of each epoch
        eval_steps=None,  # Don't evaluate during epoch (saves time)
        
        # Saving - save more frequently for small dataset
        save_strategy="epoch",
        save_steps=None,
        save_total_limit=2,

        # Performance
        optim="adamw_8bit",
        seed=42,
    ),
)

print("\n🚀 Starting SFT training...")
print("=" * 50)
trainer_stats = trainer.train()

# Print training summary
print("\n" + "=" * 50)
print("  TRAINING COMPLETE!")
print("=" * 50)
print(f"  Training loss:    {trainer_stats.training_loss:.4f}")
print(f"  Training time:    {trainer_stats.metrics['train_runtime']:.0f} seconds")
print(f"  Samples/second:   {trainer_stats.metrics['train_samples_per_second']:.2f}")
print("=" * 50)


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 6: Save Model to Google Drive (Fast Version)
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n📁 Saving trained model to: {OUTPUT_DIR}")

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Save LoRA adapters (fast, ~50-100MB)
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"✅ LoRA adapters saved to: {OUTPUT_DIR}")

# Save training configuration
config = {
    "model_name": "unsloth/llama-3-8b-Instruct-bnb-4bit",
    "lora_config": {
        "r": 16,
        "alpha": 16,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    },
    "training_stats": {
        "loss": trainer_stats.training_loss,
        "runtime": trainer_stats.metrics['train_runtime'],
        "samples_per_second": trainer_stats.metrics['train_samples_per_second']
    }
}

import json
with open(os.path.join(OUTPUT_DIR, "training_config.json"), "w") as f:
    json.dump(config, f, indent=2)

print(f"✅ Training configuration saved to: {OUTPUT_DIR}/training_config.json")


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 7: Quick Inference Test
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 50)
print("  QUICK INFERENCE TEST")
print("=" * 50)

# Switch to inference mode
FastLanguageModel.for_inference(model)

test_queries = [
    "What should I do if my nose is bleeding?",
    "Someone fainted, what are the first aid steps?",
    "How to treat a minor burn?",
]

for query in test_queries:
    prompt = (
        f"<|begin_of_text|>"
        f"<|start_header_id|>system<|end_header_id|>\n\n"
        f"You are Arohan, a medical first aid assistant for elderly Indians. "
        f"Provide clear, numbered first aid steps using simple words.<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n"
        f"{query}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
    )

    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    outputs = model.generate(
        **inputs,
        max_new_tokens=200,
        temperature=0.1,
        do_sample=True,
        top_p=0.9,
    )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract only the assistant's response
    if "assistant" in response:
        response = response.split("assistant")[-1].strip()

    print(f"\n🧑 Q: {query}")
    print(f"🤖 A: {response[:300]}")
    print("-" * 50)

print("\n✅ Training and testing complete!")
print(f"Model saved at: {OUTPUT_DIR}")
print("\n📋 Next Steps:")
print("1. Download the model from Google Drive")
print("2. Use it locally with inference scripts")
print("3. For GGUF conversion, run a separate script after training")