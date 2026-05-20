## RAG and Fine-Tuning Notes

This backend currently supports retrieval-augmented generation over multiple knowledge sources:

- `arohan`: in-memory health and first-aid documents from this repo
- `sashwat`: external persisted Chroma database at `D:\intern\medical-rag-llm\db\my_chroma_db`
- `harshita`: local FAISS index in `backend/app/knowledge_base/harshita_faiss_index`
- `geshna`: local FAISS index in `backend/app/knowledge_base/geshna_faiss`
- `all`: combines every available source

### Important practical point

This repository does **not** include an LLM fine-tuning training pipeline.
What it has today is:

- vector databases / FAISS indexes for RAG
- prompt-based answer generation using Groq-hosted models

That means Sashwat's message is consistent with the codebase: his path is an external Chroma store used for retrieval, not a local fine-tunable model in this repo.

### Best candidates for your task

If you need to work on assets that are actually available inside this repo, prefer:

- `harshita`: local JSON-backed first-aid corpus plus FAISS builder script
- `geshna`: local FAISS index available in the repository

Harshita is especially useful because the source dataset is visible at:

- `backend/app/knowledge_base/harshita_first_aid.json`
- rebuild script: `backend/app/knowledge_base/build_harshita_index.py`

### API usage

`POST /api/v1/ai/text-query` and `POST /api/v1/ai/guided-query` now accept:

```json
{
  "text": "my hand is paining",
  "context": "",
  "language": "en",
  "rag_source": "harshita"
}
```

Allowed `rag_source` values:

- `all`
- `arohan`
- `sashwat`
- `harshita`
- `geshna`
