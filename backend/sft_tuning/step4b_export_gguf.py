"""
step4b_export_gguf.py — Separate script to export trained model to GGUF format.
Run this AFTER the main training completes to avoid blocking the training process.

Usage:
1. First complete training with step4_sft_train_colab_optimized.py
2. Then run this script in a new Colab cell or as a separate script
"""

import os
import torch
from unsloth import FastLanguageModel

# ═══════════════════════════════════════════════════════════════════════════════
# CELL: Load Trained Model & Export to GGUF
# ═══════════════════════════════════════════════════════════════════════════════

# Paths
OUTPUT_DIR = "/content/drive/MyDrive/arohan_sft_model"
GGUF_DIR = os.path.join(OUTPUT_DIR, "gguf")

print(f"Loading trained model from: {OUTPUT_DIR}")

# Load the trained LoRA model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=OUTPUT_DIR,
    max_seq_length=2048,
    load_in_4bit=False,  # Use full precision for export
    dtype=torch.bfloat16,
)

print("✅ Trained model loaded successfully!")

# ═══════════════════════════════════════════════════════════════════════════════
# GGUF Export (This takes time - expect 10-30 minutes)
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n🔄 Exporting to GGUF format...")
print("⚠️  This will take 10-30 minutes - please be patient!")

# Create GGUF directory
os.makedirs(GGUF_DIR, exist_ok=True)

# Export to GGUF - this is the slow part
model.save_pretrained_gguf(
    GGUF_DIR,
    tokenizer,
    quantization_method="q4_k_m",  # Good balance of quality vs size (~4.5GB)
)

print(f"✅ GGUF export completed!")
print(f"📁 GGUF model saved to: {GGUF_DIR}")

# List the exported files
print("\n📂 Exported files:")
gguf_files = [f for f in os.listdir(GGUF_DIR) if f.endswith('.gguf')]
for file in gguf_files:
    file_path = os.path.join(GGUF_DIR, file)
    file_size = os.path.getsize(file_path) / (1024**3)  # Size in GB
    print(f"  - {file} ({file_size:.2f} GB)")

print(f"\n🚀 To use with Ollama:")
print(f"1. Download the .gguf file from Google Drive")
print(f"2. Create a Modelfile with these contents:")
print(f""")
FROM {GGUF_DIR}/your-model-file.gguf
TEMPLATE """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are Arohan, a medical first aid assistant for elderly Indians. Provide clear, numbered first aid steps using simple words.<|eot_id|><|start_header_id|>user<|end_header_id|>

{{.Prompt}}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
PARAMETER temperature 0.7
PARAMETER top_p 0.9
""")
print(f"3. Run: ollama create arohan-medical -f Modelfile")
print(f"4. Test: ollama run arohan-medical")

print(f"\n✅ GGUF export complete!")