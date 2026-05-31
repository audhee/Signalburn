# Arohan LLM Fine-Tuning — Final Integration Report

## Overview

This report documents the complete fine-tuning pipeline for the Arohan medical first aid assistant. Three workstreams have been integrated into a single, unified pipeline.

| Workstream | Person | Status | Deliverables |
|------------|--------|--------|-------------|
| SFT Dataset + Pipeline | Vaibhav | **Done** | 1,156 Q&A pairs, step1-step5 scripts, production system prompt |
| PEFT / QLoRA | Amulya | **Done** | QLoRA training script, 3 hyperparameter configs, inference script |
| DPO + Prompt Engineering | Anisha | **Done** | 47 DPO preference pairs, DPO training script, `medical_safe` template integrated into production |
| **Integration** | **All** | **Done** | Unified pipeline, comprehensive evaluation, this report |

---

## 1. Dataset

### SFT Dataset (step2 + step3)

| Metric | Before (Old) | After (New) |
|--------|-------------|-------------|
| Total pairs | 24 | **1,156** |
| Training split | ~21 | **1,040** |
| Validation split | ~3 | **116** |
| Sources | 1 Punjab textbook PDF | **3 curated sources** |
| "Section X" artifacts | Pervasive | **None** |
| Emergency handling | Never present | Always present |
| Numbered first aid steps | Rare | Every answer |

**Sources used:**
- `first_aid_data.py` — 50+ structured first aid records (wound care, burns, bleeding)
- `harshita_first_aid.json` — 200+ real-world Indian first aid scenarios
- `health_data.py` — Vital signs, chronic conditions, emergency response

**Method:** Programmatic generation from structured data — no LLM calls, so no hallucination or textbook poisoning.

### DPO Preference Dataset (step4b)

| Metric | Before (Anisha's original) | After (Expanded) |
|--------|---------------------------|------------------|
| Total pairs | 3 | **47** |
| Training split | 3 | **42** |
| Validation split | 0 | **5** |

**Preference patterns covered:**
| Pattern | Pairs | Example Rejected |
|---------|-------|-----------------|
| Dangerous advice | 41 | "Apply ice directly to burn" |
| Textbook jargon | 6 | "Refer to section 14.2" |

**Scenarios covered:**
Bleeding, Burns, Fractures, Choking, Heart Attack, Stroke, Fainting, Allergic Reactions, Poisoning, Snake Bite, Dog Bite, Heat Stroke, Asthma, Seizure, Electric Shock, Drowning, Hypothermia, Head Injury, Eye Injury, Fever, Panic Attack, Hypoglycemia, Diarrhea/Vomiting, Spinal Injury.

### Dataset Location

All datasets are in `backend/sft_tuning/sft_data/`:
- `sft_dataset_train.jsonl` — SFT training (1,040 pairs)
- `sft_dataset_val.jsonl` — SFT validation (116 pairs)
- `dpo_dataset_train.jsonl` — DPO training (42 pairs)
- `dpo_dataset_val.jsonl` — DPO validation (5 pairs)
- `dpo_data_raw.jsonl` — Full DPO dataset (47 pairs)

---

## 2. Training Pipeline

### Stage 1: QLoRA (SFT) — Amulya's PEFT

**Script:** `step4_qlora_train.py`

Trains on SFT dataset using QLoRA on a free Google Colab T4 GPU.

| Experiment | r | lora_alpha | epochs | lr | Expected VRAM |
|------------|---|------------|--------|----|---------------|
| baseline | 8 | 16 | 1 | 2e-4 | ~10-11 GB |
| **medium** | **16** | **32** | **3** | **2e-4** | **~11-12 GB** |
| high | 32 | 64 | 5 | 1e-4 | ~12-14 GB |

**Output:** LoRA adapter (~50 MB) saved to Google Drive.

### Stage 2: DPO — Anisha's Alignment

**Script:** `step4c_dpo_train.py`

Applies Direct Preference Optimization ON TOP of the QLoRA adapter.

| Hyperparameter | Value |
|----------------|-------|
| Beta (DPO temp) | 0.1 |
| Learning rate | 5e-6 |
| Epochs | 2 |
| Effective batch | 8 |

**Input:** QLoRA adapter → **Output:** DPO + QLoRA adapter

### Stage 3: Full Pipeline Orchestrator

**Script:** `pipeline_full_finetune.py`

Single entry point:
```bash
python pipeline_full_finetune.py --stage all
```

Stages:
```
Dataset Verify → QLoRA (SFT) → DPO (Alignment) → Evaluation
```

---

## 3. Production Integration

### Current Production Setup

Arohan uses **Groq (llama-3.3-70b-versatile)** with Anisha's `medical_safe` system prompt in `llm_service.py`:

- **3-layer script protection** — wrong-language detection + retry + hardcoded fallback
- **RAG context injection** — retrieved from FAISS knowledge base
- **Emergency detection** — flagging urgent cases for priority response
- **5 language modes** — English, Hindi, Kannada, Hinglish, Kanglish

### Fine-Tuned Model Integration Options

| Method | Description | When to Use |
|--------|-------------|-------------|
| **A) Cloud (Groq)** | Current production. No changes needed. | ✅ **Recommended for production now** |
| **B) Local (Ollama)** | Run SFT model locally via Ollama | Fallback / offline mode |
| **C) Hybrid** | Env flag to toggle Groq ↔ local | Development / testing |
| **D) Hugging Face Hub** | Upload adapters and load via PEFT | Scaling / sharing |

**Recommended path:** Option C (Hybrid) — use Groq for production, toggle to QLoRA/DPO model for testing.

---

## 4. Evaluation Framework

### Golden Cases (`backend/evals/golden_cases.json`)

| Suite | Cases | Description |
|-------|-------|-------------|
| smoke | 5 | Critical path: English HI, Hindi, emergency detection |
| core | 6 | Language lock, multilingual queries, transcription |
| full | 6 | Safety checks, multimodal, chat history |

### Comprehensive Eval Script (`step5_evaluate_comprehensive.py`)

Tests **20 diverse cases** across all models:

| Test Category | Count |
|---------------|-------|
| Standard first aid (English) | 14 |
| Multilingual (Hinglish, Kanglish) | 5 |
| Multi-symptom / comprehension | 1 |
| Emergency scenarios | 10 |

**Quality dimensions scored:**
1. Numbered first aid steps (25% weight)
2. Emergency number mention (20%)
3. Call/ambulance instruction (10%)
4. No disease diagnosis (15%)
5. Simple language / no jargon (10%)
6. Script purity (10%)
7. Response length / substance (10%)

---

## 5. Pipeline Output Files

| File | Purpose |
|------|---------|
| `backend/sft_tuning/` | |
| `step2_generate_sft_pairs.py` | Generate 1,156 SFT pairs from structured data |
| `step3_prepare_dataset.py` | Format + split into train/val |
| `step4_qlora_train.py` | QLoRA training (Amulya's PEFT) |
| `step4b_expand_dpo_data.py` | Expand DPO from 3→47 pairs |
| `step4c_dpo_train.py` | DPO training on top of QLoRA |
| `pipeline_full_finetune.py` | Unified orchestrator |
| `step5_evaluate_comprehensive.py` | Multi-model evaluation |
| `inference_qlora.py` | Local inference with adapter |
| `peft_report.md` | PEFT technical documentation |
| `backend/sft_tuning/sft_data/` | |
| `sft_dataset_train.jsonl` | SFT training (1,040 pairs) |
| `sft_dataset_val.jsonl` | SFT validation (116 pairs) |
| `dpo_dataset_train.jsonl` | DPO training (42 pairs) |
| `dpo_dataset_val.jsonl` | DPO validation (5 pairs) |
| `backend/evals/` | |
| `golden_cases.json` | 17 test cases across 3 suites |
| `comprehensive_eval_report.json` | Generated after eval run |
| `backend/app/services/ai/` | |
| `llm_service.py` | Production LLM service with Anisha's prompt |

---

## 6. Summary

```
Data Pipeline (Vaibhav)
    ↓
1,156 quality Q&A pairs
    ↓
QLoRA SFT Training (Amulya)
    ↓
LoRA adapter (50 MB)
    ↓
DPO Preference Alignment (Anisha)
    ↓
47 preference pairs → Aligned adapter
    ↓
Comprehensive Evaluation
    ↓
Groq Production ↔ QLoRA ↔ QLoRA+DPO Comparison
```

**All three workstreams are now integrated into a single, auditable pipeline.**
