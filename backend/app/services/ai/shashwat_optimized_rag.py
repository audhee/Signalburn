"""
Shashwat optimized RAG runtime adapter.

Ports the updated medical-rag-llm retrieval behavior into Arohan:
- all-MiniLM-L6-v2 normalized CPU embeddings
- persisted Chroma DB
- MMR retrieval with k=4, fetch_k=10
- route-isolated retrieval for multi-part questions
"""

import logging
import os
from typing import List, Optional
from pathlib import Path

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from app.services.ai.download_chroma import ensure_chroma_db
from app.core.config import settings
print("========== SHASHWAT_OPTIMIZED_RAG FILE LOADED ==========")

logger = logging.getLogger(__name__)


def _load_chroma_class():
    try:
        from langchain_chroma import Chroma
        return Chroma
    except Exception:
        from langchain_community.vectorstores import Chroma
        return Chroma


class ShashwatOptimizedRAG:
    def __init__(self) -> None:
        self.db = None
        self.retriever = None
        self.embedding_model = None
        self.chroma_dir = settings.SASHWAT_CHROMA_DIR
        self._initialize()

    def _resolve_chroma_dir(self) -> str:
        configured = Path(self.chroma_dir)

        # Priority 1: SASHWAT_CHROMA_DIR env var explicitly set by user
        # (e.g., Railway volume mount with dedicated ChromaDB)
        env_var_explicit = os.environ.get("SASHWAT_CHROMA_DIR") is not None
        if env_var_explicit and configured.exists():
            return str(configured)

        # Priority 2: knowledge_base/sashwat_chroma_db (has ~53K documents)
        # Canonical source of medical RAG data — preferred default
        kb_chroma = Path(__file__).parent.parent.parent / "knowledge_base" / "sashwat_chroma_db"
        if kb_chroma.exists():
            return str(kb_chroma)

        # Priority 3: Default configured path (my_chroma_db) or alternate paths
        if configured.exists():
            return str(configured)

        candidates = []
        if configured.name == "my_chroma_db" and configured.parent.name == "db":
            candidates.append(configured.parent.parent / "my_chroma_db")
        elif configured.name != "my_chroma_db":
            candidates.append(configured / "my_chroma_db")

        for candidate in candidates:
            if candidate.exists():
                return str(candidate)

        return str(configured)

    def _initialize(self) -> None:
        print("========== SHASHWAT RAG INITIALIZE STARTED ==========")

        db_path = ensure_chroma_db()
        if db_path:
            self.chroma_dir = db_path
        else:
            self.chroma_dir = self._resolve_chroma_dir()

        print(f"DEBUG CHROMA PATH = {self.chroma_dir}")
        print(f"DEBUG EXISTS = {os.path.exists(self.chroma_dir)}")

        if not self.chroma_dir or not os.path.exists(self.chroma_dir):
            print(f"DEBUG DB NOT FOUND = {self.chroma_dir}")
            logger.warning("Shashwat optimized Chroma DB not found at %s", self.chroma_dir)
            return

        try:
            print("DEBUG LOADING EMBEDDINGS")

            self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
            )

            print("DEBUG EMBEDDINGS LOADED")

            Chroma = _load_chroma_class()

            print("DEBUG OPENING CHROMA DB")

            db_file = Path(self.chroma_dir) / "chroma.sqlite3"

            with open(db_file, "rb") as f:
                first_bytes = f.read(100)

            print(f"FIRST_100_BYTES = {first_bytes}")

            Chroma = _load_chroma_class()

            self.db = Chroma(
                persist_directory=self.chroma_dir,
                embedding_function=self.embedding_model,
            )

            print("DEBUG CHROMA OPENED SUCCESSFULLY")

            self.retriever = self.db.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 4, "fetch_k": 10},
            )

            print("DEBUG RETRIEVER CREATED")

            logger.info("Shashwat optimized RAG ready with MMR retrieval.")

        except Exception as exc:
            print(f"DEBUG CHROMA ERROR = {exc}")
            logger.error("Failed to load Shashwat optimized RAG: %s", exc)
            self.db = None
            self.retriever = None
    @staticmethod
    def deconstruct_query(query: str) -> List[str]:
        clean = (query or "").strip()
        if not clean:
            return []

        sub_queries = [part.strip() + "?" for part in clean.split("?") if part.strip()]
        if len(sub_queries) <= 1 and "," in clean:
            sub_queries = [part.strip() for part in clean.split(",") if part.strip()]

        return sub_queries or [clean]

    def retrieve_documents(self, query: str) -> List[Document]:
        if not self.retriever:
            return []

        docs: List[Document] = []
        for sub_query in self.deconstruct_query(query):
            try:
                if hasattr(self.retriever, "invoke"):
                    route_docs = self.retriever.invoke(sub_query)
                else:
                    route_docs = self.retriever.get_relevant_documents(sub_query)
                for doc in route_docs:
                    doc.metadata = dict(doc.metadata or {})
                    doc.metadata["route_query"] = sub_query
                docs.extend(route_docs)
            except Exception as exc:
                logger.error("Shashwat retrieval failed for '%s': %s", sub_query, exc)

        return self._dedupe_documents(docs)

    @staticmethod
    def _dedupe_documents(docs: List[Document]) -> List[Document]:
        seen = set()
        unique_docs = []
        for doc in docs:
            key = (
                doc.metadata.get("source"),
                doc.metadata.get("page"),
                doc.metadata.get("chunk_index"),
                doc.page_content[:120],
            )
            if key in seen:
                continue
            seen.add(key)
            unique_docs.append(doc)
        return unique_docs

    def retrieve_context(self, query: str, k: Optional[int] = None) -> str:
        docs = self.retrieve_documents(query)
        if k:
            docs = docs[:k]
        if not docs:
            return ""

        context_blocks = []
        for idx, doc in enumerate(docs, start=1):
            source = doc.metadata.get("source", "Unknown")
            route = doc.metadata.get("route_query", query)
            context_blocks.append(
                f"[Shashwat route {idx} | source: {source} | query: {route}]\n"
                f"{doc.page_content}"
            )
        logger.info("Shashwat optimized RAG returned %s chunks.", len(context_blocks))
        return "\n\n".join(context_blocks)


shashwat_optimized_rag = ShashwatOptimizedRAG()
