"""
build_optimized_index.py -- Optimized RAG Ingest Script
========================================================
Based on Sashwat's medical-rag-llm ingest.py approach:
  - Uses llama-index framework instead of raw langchain
  - Uses FAISS vector store (faster, more scalable)
  - Uses better embedding model: BAAI/bge-small-en-v1.5
  - Stores rich metadata (category, id, title, severity, tags)

Usage:
    cd backend && python -m app.knowledge_base.build_optimized_index
"""

import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("optimized_index")

INDEX_DIR = Path(__file__).parent / "optimized_faiss"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"


def build_optimized_index():
    from llama_index.core import Document as LIDocument, VectorStoreIndex, Settings
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.vector_stores.faiss import FaissVectorStore
    import faiss

    logger.info(f"Loading embedding model: {EMBED_MODEL}")
    embed_model = HuggingFaceEmbedding(
        model_name=EMBED_MODEL,
        embed_batch_size=32,
        device="cpu",
    )
    Settings.embed_model = embed_model
    logger.info("Embedding model loaded.")

    from app.knowledge_base.first_aid_data import get_all_first_aid_documents
    from app.knowledge_base.health_data import HEALTH_KNOWLEDGE_BASE

    all_docs = get_all_first_aid_documents()
    logger.info(f"Loaded {len(all_docs)} first-aid documents from KB.")

    li_docs = []
    for doc in all_docs:
        metadata = {
            "id": doc.get("id", ""),
            "title": doc.get("title", ""),
            "category": doc.get("category", ""),
            "wound_type": doc.get("wound_type", ""),
            "severity": doc.get("severity_applicable", "minor"),
            "tags": ", ".join(doc.get("tags", [])),
            "source": "arohan_first_aid_kb",
        }
        li_docs.append(LIDocument(text=doc["content"], metadata=metadata))

    for i, text in enumerate(HEALTH_KNOWLEDGE_BASE):
        li_docs.append(LIDocument(
            text=text,
            metadata={
                "id": f"health_kb_{i}",
                "title": "Health Knowledge",
                "category": "general_health",
                "severity": "general",
                "tags": "health, vitals, monitoring",
                "source": "arohan_health_kb",
            }
        ))

    logger.info(f"Total llama-index documents created: {len(li_docs)}")

    dimension = 384
    faiss_index = faiss.IndexFlatIP(dimension)
    vector_store = FaissVectorStore(faiss_index=faiss_index)

    logger.info("Building FAISS index with llama-index...")
    index = VectorStoreIndex.from_documents(
        li_docs,
        vector_store=vector_store,
        show_progress=True,
    )
    logger.info("FAISS index built successfully.")

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    index.storage_context.persist(str(INDEX_DIR))
    logger.info(f"Optimized index saved to {INDEX_DIR}")

    total_vectors = faiss_index.ntotal
    print(f"\n{'='*60}")
    print(f"Optimized FAISS index built successfully!")
    print(f"   Location: {INDEX_DIR}")
    print(f"   Documents: {len(li_docs)}")
    print(f"   Vectors:   {total_vectors}")
    print(f"   Model:     {EMBED_MODEL}")
    print(f"{'='*60}")

    print("\nQuick retrieval test:")
    retriever = index.as_retriever(similarity_top_k=3)
    test_queries = [
        "my nose is bleeding",
        "a scorpion stung me on my foot",
        "i cut my hand on a sharp rock and blood is pouring out",
        "a snake just bit my friend on the leg",
    ]
    for q in test_queries:
        nodes = retriever.retrieve(q)
        print(f"\n  Query: {q}")
        for node in nodes:
            score = node.score if hasattr(node, 'score') else '?'
            title = node.metadata.get("title", "N/A")
            print(f"    [{score:.3f}] {title[:60]}")


if __name__ == "__main__":
    build_optimized_index()
