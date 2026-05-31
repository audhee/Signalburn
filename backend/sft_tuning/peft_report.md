# PEFT / QLoRA Training Report — Amulya's Deliverable

## Overview

**Technique:** QLoRA (Quantized Low-Rank Adaptation)  
**Base Model:** Llama 3 8B Instruct  
**Training Method:** Parameter-Efficient Fine-Tuning (PEFT)  
**Trainable Parameters:** ~0.08% of total model (~6M out of 8B)

Instead of training all 8 billion parameters (expensive, needs 80GB+ GPU), QLoRA freezes the base model in 4-bit and trains only small adapter layers attached to attention and MLP modules. This enables training on a free Google Colab T4 GPU (16GB VRAM).

---

## How QLoRA Works

```
┌─────────────────────────────────────────────────┐
│  Base Model (4-bit NormalFloat, FROZEN)          │
│  ┌───────────────────────────────────────────┐  │
│  │ Attention Layers: q_proj, k_proj, v_proj,  │  │
│  │                o_proj                       │  │
│  │ MLP Layers: gate_proj, up_proj, down_proj  │  │
│  └───────────────────────────────────────────┘  │
│         │  │  │                          │  │  │
│         ▼  ▼  ▼                          ▼  ▼  ▼  ← LoRA adapters
│  ┌───────────────────────────────────────────┐  │   (trainable in fp16)
│  │ LoRA_A (r × d) @ LoRA_B (d × r)           │  │
│  │  → ΔW = LoRA_A · LoRA_B                    │  │
│  │  → Output = W₀ · x + ΔW · x                 │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

**Key insight:** When you multiply LoRA_A (r×d) by LoRA_B (d×r), you get a full-rank update ΔW but only store 2×r×d parameters instead of d². With r=16 and d=4096, that's ~131K parameters per module instead of 16M.

---

## Dataset

| Metric | Value |
|--------|-------|
| Training samples | 1,040 |
| Validation samples | 116 |
| Source | First aid knowledge bases (harshita_first_aid.json, first_aid_data.py, health_data.py) |
| Format | Alpaca-style with Llama 3 chat template |
| Quality | No "section X" references, proper numbered steps, emergency handling present |

### Sample Training Pair

```
System: You are Arohan, a medical first aid assistant for elderly Indians.
         Provide clear, numbered first aid steps using simple words. ...

User: What should I do for a nosebleed suddenly started?

Assistant: Blood coming from nose.

What to do:
1. Sit upright.
2. Lean slightly forward.
3. Pinch nose for 10 minutes.

What NOT to do:
1. Do not tilt head back.

When to seek help:
If bleeding continues after 15 minutes.
Call 112 or 108 if condition worsens or does not improve.
```

---

## Hyperparameter Experiments

Run each experiment by changing `ACTIVE_EXPERIMENT` in `step4_qlora_train.py` and log results.

### Experiment Configuration

| Name | r | lora_alpha | lora_dropout | epochs | learning_rate | Expected VRAM |
|------|---|------------|-------------|--------|---------------|---------------|
| **baseline** | 8 | 16 | 0.0 | 1 | 2e-4 | ~10-11 GB |
| **medium** | 16 | 32 | 0.0 | 3 | 2e-4 | ~11-12 GB |
| **high** | 32 | 64 | 0.05 | 5 | 1e-4 | ~12-14 GB |

### Results Table (Fill After Running)

| Experiment | Train Loss | Runtime (s) | Samples/sec | Peak VRAM | Quality (1-5) |
|------------|-----------|-------------|-------------|-----------|---------------|
| baseline | ? | ? | ? | ? | ? |
| medium | ? | ? | ? | ? | ? |
| high | ? | ? | ? | ? | ? |

Fill the `hyperparameter_experiments.json` file by running each experiment sequentially.

---

## Files Created

| File | Purpose |
|------|---------|
| `step4_qlora_train.py` | QLoRA training script (run on Colab) |
| `inference_qlora.py` | Local inference with adapter (CPU or GPU) |
| `peft_report.md` | This document |
| `ollama_deploy/` | Deployment configuration for Ollama (step5) |

---

## How to Run

### Step 1: Upload Dataset to Google Drive

```bash
# Upload backend/sft_tuning/sft_data/ to /content/drive/MyDrive/arohan_sft_data/
```

### Step 2: Run QLoRA Training on Colab

```python
# Open step4_qlora_train.py in Colab, run cell by cell.
# Change ACTIVE_EXPERIMENT to "baseline", "medium", or "high"
# Adapter saves to: /content/drive/MyDrive/arohan_qlora_adapter/
```

### Step 3: Test Locally

```bash
# CPU (works with any machine):
python inference_qlora.py --adapter ./arohan_qlora_adapter/experiment_medium

# GPU:
python inference_qlora.py --adapter ./arohan_qlora_adapter/experiment_medium --device cuda

# Compare with Groq production:
python inference_qlora.py --adapter ./arohan_qlora_adapter/experiment_medium --compare-groq

# Single query:
python inference_qlora.py --adapter ./arohan_qlora_adapter/experiment_medium --query "nosebleed treatment"
```

### Step 4: Upload to Hugging Face Hub

```python
from huggingface_hub import HfApi
api = HfApi()
api.upload_folder(
    folder_path="./arohan_qlora_adapter/experiment_medium",
    repo_id="your-username/arohan-medical-qlora",
    repo_type="model",
)
```

---

## Integration into Arohan

The trained adapter can be loaded into Arohan's `llm_service.py`:

```python
# In backend/app/services/ai/llm_service.py
from peft import PeftModel
from unsloth import FastLanguageModel

def load_qlora_model():
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/llama-3-8b-Instruct-bnb-4bit",
        max_seq_length=2048,
        load_in_4bit=True,
    )
    model = PeftModel.from_pretrained(model, "./adapter/experiment_medium")
    FastLanguageModel.for_inference(model)
    return model, tokenizer
```

---

## Performance Comparison

| Method | Trainable Params | VRAM Needed | Training Time (T4) | File Size |
|--------|-----------------|-------------|-------------------|-----------|
| Full Fine-Tuning | 8B (100%) | ~80GB | N/A (can't run) | N/A |
| LoRA (16-bit) | ~6M (0.08%) | ~24GB | ~30 min | 50 MB |
| **QLoRA (4-bit)** | **~6M (0.08%)** | **~12GB** | **~10 min** | **50 MB** |

QLoRA is the only method that fits on a free Colab T4 (16GB VRAM).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Out of memory on T4 | Use "baseline" config (r=8, epochs=1) |
| CUDA not available | You need to run on Colab, not locally |
| Adapter file not found | Check the path — should point to subfolder with adapter_model.safetensors |
| Model gives "section X" references | Dataset was rebuilt — this shouldn't happen with the new data |
| Slow on CPU | Use --device cuda or reduce to 1-2 test queries |
