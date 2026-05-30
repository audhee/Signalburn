# Arohan RAG & Fine-Tuning Documentation

## Optimized RAG Pipeline

This backend uses a **two-tier RAG system** for retrieval-augmented generation:

### Tier 1: Optimized FAISS Index (llama-index + bge-small-en-v1.5)
- **Location**: `backend/app/knowledge_base/optimized_faiss/`
- **Framework**: `llama-index` with `HuggingFaceEmbedding` (`BAAI/bge-small-en-v1.5`)
- **Vector Store**: FAISS (faster, more scalable than Chroma)
- **Top-k**: 5
- **Auto-loaded** on startup by `rag_service.py`
- **Rebuild command**: `cd backend && python -m app.knowledge_base.build_optimized_index`

### Tier 2: Legacy Stores (fallback)
| Store | Source | Engine |
|-------|--------|--------|
| `arohan` | `first_aid_data.py` (72 docs) + `health_data.py` (21 docs) | langchain + Chroma (all-MiniLM-L6-v2) |
| `sashwat` | `D:\intern\medical-rag-llm\db\my_chroma_db` | External persisted Chroma |
| `harshita` | `backend/app/knowledge_base/harshita_faiss_index/` | Local FAISS |
| `geshna` | `backend/app/knowledge_base/geshna_faiss/` | Local FAISS |

### Retrieval Priority
When `source="all"`, the optimized FAISS index is queried **first**, then augmented with legacy stores.

## Fine-Tuned Ollama Model

- **GGUF model**: `backend/sft_tuning/ollama_deploy/arohan-medical-sft.gguf`
- **Modelfile**: `backend/sft_tuning/ollama_deploy/Modelfile`
- **Setup script**: `backend/sft_tuning/ollama_deploy/setup_ollama.bat`
- **Toggle**: `USE_LOCAL_MODEL=true` env var in `.env`

## Dual Mode Architecture

```
User Input → process_voice_with_llm()
              ├── USE_LOCAL_MODEL=true  → process_voice_with_ollama()
              └── USE_LOCAL_MODEL=false → Groq llama-3.3-70b-versatile
```

Both paths share the same `build_system_prompt()` from `prompt_utils.py` and the same RAG context.

## Directory Structure (Consolidated)

```
backend/
├── app/
│   ├── services/ai/
│   │   ├── prompt_utils.py        ← Shared prompts, script validation, fallbacks
│   │   ├── llm_service.py         ← Groq path (USE_LOCAL_MODEL=false)
│   │   ├── ollama_service.py      ← Local Ollama path (USE_LOCAL_MODEL=true)
│   │   ├── rag_service.py         ← RAG: optimized FAISS + legacy stores
│   │   └── language_service.py    ← Language detection + normalization
│   ├── knowledge_base/
│   │   ├── first_aid_data.py      ← 93 first-aid + health documents
│   │   ├── health_data.py
│   │   ├── build_optimized_index.py  ← Rebuild script for optimized FAISS
│   │   ├── optimized_faiss/       ← Persistent FAISS index (Tier 1)
│   │   ├── harshita_faiss_index/  ← Legacy (Tier 2)
│   │   └── geshna_faiss/         ← Legacy (Tier 2)
│   └── core/config.py             ← Centralized settings
├── sft_tuning/                    ← Full fine-tuning pipeline + Ollama deploy
│   ├── ollama_deploy/
│   │   ├── arohan-medical-sft.gguf
│   │   ├── Modelfile
│   │   ├── setup_ollama.bat
│   │   └── INTEGRATION_GUIDE.md
│   ├── step1_extract_rag_data.py
│   ├── step2_generate_sft_pairs.py
│   ├── step3_prepare_dataset.py
│   ├── step4_qlora_train.py
│   ├── step4c_dpo_train.py
│   └── ...
├── DUAL_MODE_README.md
└── requirements.txt
```

## API Usage

```json
POST /api/v1/ai/text-query
{
  "text": "my hand is paining",
  "context": "",
  "language": "en",
  "rag_source": "optimized"   // or "all", "arohan", "sashwat", "harshita", "geshna"
}
```
