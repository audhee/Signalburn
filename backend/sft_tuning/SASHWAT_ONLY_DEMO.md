# Sashwat-Only SFT Demo

Use this flow when the requirement is to build the LLM tuning dataset only from Sashwat's RAG database.

## What This Uses

- Input RAG DB: `D:\intern\medical-rag-llm\db\my_chroma_db`
- Extracted chunks: `backend/sft_tuning/sft_data/raw_chunks.jsonl`
- SFT raw pairs: `backend/sft_tuning/sft_data/sft_pairs_raw.jsonl`
- Train split: `backend/sft_tuning/sft_data/sft_dataset_train.jsonl`
- Validation split: `backend/sft_tuning/sft_data/sft_dataset_val.jsonl`

## Run This Demo

From repo root:

```powershell
python backend\sft_tuning\step1_extract_rag_data.py
python backend\sft_tuning\step2b_generate_sft_pairs_from_sashwat_chunks.py
python backend\sft_tuning\step3_prepare_dataset.py
```

For the full integrated local prep, run:

```powershell
python backend\sft_tuning\run_integrated_local_prep.py
```

Expected current output:

- `step1`: extracts about `53,498` chunks from Sashwat's Chroma DB
- `step2b`: keeps `535` clear Q/A pairs from Sashwat chunks
- `step3`: prepares `518` quality pairs
- Train split: `466`
- Validation split: `52`

## Verify Sources

```powershell
python backend\sft_tuning\verify_sashwat_only.py
```

All three files should show only:

```text
{'sashwat_chroma': ...}
```

## Query Demo

Use this if your mentor asks to enter a query and see a response:

```powershell
python backend\sft_tuning\demo_sashwat_query.py "What is malaria?"
python backend\sft_tuning\demo_sashwat_query.py "How is gastroenteritis managed at home?"
python backend\sft_tuning\demo_sashwat_query.py "What are symptoms of tuberculosis?"
```

This searches the Sashwat-only SFT pairs and returns the closest prepared response. It is a dataset retrieval demo, not final fine-tuned model inference.

## What To Say In Meeting

"For the Sashwat-only path, we extract chunks directly from Sashwat's Chroma RAG database, convert only explicit Q/A chunks into instruction-output SFT pairs, then prepare train/validation JSONL files for QLoRA/SFT training. We are not using Harshita or Geshna in this path."
