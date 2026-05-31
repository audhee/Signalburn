# Integrated Fine-Tuning Runbook

This is the integrated workflow for all three contributors.

## Team Split

- Vaibhav: Sashwat-only SFT dataset from `D:\intern\medical-rag-llm\db\my_chroma_db`
- Amulya: QLoRA / PEFT training using `step4_qlora_train.py`
- Anisha: DPO preference alignment using `step4c_dpo_train.py` plus medical-safe prompt behavior in the backend

## Local Prep

Run this from repo root:

```powershell
python backend\sft_tuning\run_integrated_local_prep.py
```

This runs:

- `step1_extract_rag_data.py`
- `step2b_generate_sft_pairs_from_sashwat_chunks.py`
- `step3_prepare_dataset.py`
- `step4b_expand_dpo_data.py`
- `verify_sashwat_only.py`

Expected current SFT output:

- Raw Sashwat chunks: about `53,498`
- Sashwat SFT pairs: `535`
- Quality SFT pairs: `518`
- Train split: `466`
- Validation split: `52`
- Source verification: only `sashwat_chroma`

Expected DPO output:

- DPO pairs: `47`
- DPO train: `42`
- DPO validation: `5`

## Colab Training

Upload `backend/sft_tuning/sft_data/` to:

```text
/content/drive/MyDrive/arohan_sft_data/
```

Then run:

```bash
python pipeline_full_finetune.py --stage all
```

This runs:

- QLoRA SFT training using Amulya's PEFT script
- DPO alignment using Anisha's script
- Evaluation using the comprehensive evaluator

## Backend Integration

After exporting the trained GGUF and creating the Ollama model:

```powershell
set USE_LOCAL_MODEL=true
set OLLAMA_MODEL=arohan-medical
python -m uvicorn app.main:app --reload
```

The backend routes through `llm_service.py`, which switches between Groq and local Ollama using `USE_LOCAL_MODEL`.

