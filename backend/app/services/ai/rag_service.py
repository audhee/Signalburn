import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain_core.documents import Document
from app.core.config import settings
from app.knowledge_base.health_data import HEALTH_KNOWLEDGE_BASE
from app.knowledge_base.first_aid_data import FIRST_AID_DOCUMENTS
from app.services.ai.shashwat_optimized_rag import shashwat_optimized_rag

logger = logging.getLogger(__name__)

# Paths to all databases
SASHWAT_CHROMA_DIR  = settings.SASHWAT_CHROMA_DIR
HARSHITA_FAISS_DIR  = settings.HARSHITA_FAISS_DIR
GESHNA_FAISS_DIR    = settings.GESHNA_FAISS_DIR
OPTIMIZED_INDEX_DIR = Path(__file__).parent.parent.parent / "knowledge_base" / "optimized_faiss"
VALID_RAG_SOURCES   = ("all", "arohan", "optimized", "sashwat_optimized", "sashwat", "harshita", "geshna")


class RAGService:
    def __init__(self):
        self.arohan_db     = None   # in-memory ChromaDB (health + first aid)
        self.sashwat_db    = None   # Sashwat's medical ChromaDB
        self.sashwat_optimized_db = shashwat_optimized_rag
        self.harshita_db   = None   # Harshita's FAISS (dynamic structured)
        self.geshna_db     = None   # Geshna's FAISS (question-flow based)
        self.optimized_db  = None   # Optimized FAISS via llama-index (higher quality)
        self.embedding_model = None
        self._initialize()

    def _initialize(self):
        try:
            logger.info("Initializing RAG service — loading embedding model...")

            self.embedding_model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )

            # --- 1. Optimized FAISS index (llama-index) ---
            # Uses better embeddings (BAAI/bge-small-en-v1.5) and llama-index framework
            self._load_optimized_index()

            # --- 2. Arohan in-memory KB (fallback Chroma using all-MiniLM-L6-v2) ---
            documents = [
                Document(page_content=text, metadata={"source": "arohan_health_kb"})
                for text in HEALTH_KNOWLEDGE_BASE
            ]
            first_aid_docs = [
                Document(
                    page_content=doc["content"],
                    metadata={
                        "source":   "arohan_first_aid_kb",
                        "id":       doc["id"],
                        "title":    doc["title"],
                        "category": doc["category"],
                        "severity": doc.get("severity_applicable", "minor"),
                        "tags":     ", ".join(doc.get("tags", [])),
                    }
                )
                for doc in FIRST_AID_DOCUMENTS
            ]
            all_arohan_docs = documents + first_aid_docs
            self.arohan_db = Chroma.from_documents(
                all_arohan_docs,
                self.embedding_model,
                collection_name="arohan_health_knowledge"
            )
            logger.info(f"Arohan KB ready — {len(all_arohan_docs)} docs.")

            # --- 3. Sashwat's ChromaDB ---
            if os.path.exists(SASHWAT_CHROMA_DIR):
                self.sashwat_db = Chroma(
                    persist_directory=SASHWAT_CHROMA_DIR,
                    embedding_function=self.embedding_model,
                )
                logger.info("Sashwat medical RAG DB loaded.")
            else:
                logger.warning(f"Sashwat DB not found at {SASHWAT_CHROMA_DIR}")

            # --- 4. Harshita's FAISS ---
            if os.path.exists(HARSHITA_FAISS_DIR):
                self.harshita_db = FAISS.load_local(
                    HARSHITA_FAISS_DIR,
                    self.embedding_model,
                    allow_dangerous_deserialization=True
                )
                logger.info("Harshita FAISS DB loaded.")
            else:
                logger.warning(f"Harshita FAISS not found at {HARSHITA_FAISS_DIR}")

            # --- 5. Geshna's FAISS ---
            if os.path.exists(GESHNA_FAISS_DIR):
                self.geshna_db = FAISS.load_local(
                    GESHNA_FAISS_DIR,
                    self.embedding_model,
                    allow_dangerous_deserialization=True
                )
                logger.info("Geshna FAISS DB loaded.")
            else:
                logger.warning(f"Geshna FAISS not found at {GESHNA_FAISS_DIR}")

        except Exception as e:
            logger.error(f"RAG init failed: {e}")
            self.arohan_db   = None
            self.sashwat_db  = None
            self.harshita_db = None
            self.geshna_db   = None
            self.optimized_db = None

    def _load_optimized_index(self):
        """Load the optimized FAISS index built with llama-index."""
        index_path = str(OPTIMIZED_INDEX_DIR)
        if not os.path.exists(index_path):
            logger.warning(f"Optimized index not found at {index_path}")
            logger.warning("Run: python -m app.knowledge_base.build_optimized_index")
            return

        try:
            from llama_index.core import StorageContext, load_index_from_storage, Settings
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding

            # Use BAAI/bge-small-en-v1.5 for the optimized index
            logger.info("Loading optimized FAISS index (llama-index)...")
            embed_model = HuggingFaceEmbedding(
                model_name="BAAI/bge-small-en-v1.5",
                embed_batch_size=32,
                device="cpu",
            )
            Settings.embed_model = embed_model

            storage_context = StorageContext.from_defaults(persist_dir=index_path)
            self.optimized_db = load_index_from_storage(storage_context)
            logger.info("Optimized FAISS index loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load optimized index: {e}")
            self.optimized_db = None

    def _normalize_source(self, source: Optional[str]) -> str:
        normalized = (source or "all").strip().lower()
        if normalized not in VALID_RAG_SOURCES:
            logger.warning(f"Unknown rag_source '{source}', defaulting to 'all'.")
            return "all"
        return normalized

    def _get_enabled_stores(self, source: Optional[str]) -> List[Tuple[str, object]]:
        normalized = self._normalize_source(source)
        stores: Dict[str, object] = {
            "sashwat_optimized": self.sashwat_optimized_db,
            "optimized": self.optimized_db,
            "arohan": self.arohan_db,
            "sashwat": self.sashwat_db,
            "harshita": self.harshita_db,
            "geshna": self.geshna_db,
        }
        if normalized == "all":
            return [(name, store) for name, store in stores.items() if store]
        selected_store = stores.get(normalized)
        return [(normalized, selected_store)] if selected_store else []

    def _search_store(self, store_name: str, store: object, query: str, k: int) -> List[Document]:
        if not store:
            return []
        try:
            # Shashwat's updated repo uses route-isolated MMR retrieval.
            if store_name == "sashwat_optimized":
                context = store.retrieve_context(query, k=k)
                if not context:
                    return []
                return [
                    Document(
                        page_content=context,
                        metadata={"source": "sashwat_optimized_mmr"},
                    )
                ]

            # Optimized index uses llama-index retriever
            if store_name == "optimized":
                retriever = store.as_retriever(similarity_top_k=k)
                nodes = retriever.retrieve(query)
                results = [
                    Document(
                        page_content=node.text,
                        metadata=node.metadata,
                    )
                    for node in nodes
                ]
                logger.info(f"Optimized DB: {len(results)} chunks (llama-index).")
                return results

            # All other stores use langchain similarity_search
            results = store.similarity_search(query, k=k)
            logger.info(f"{store_name.title()} DB: {len(results)} chunks.")
            return results
        except Exception as e:
            logger.error(f"{store_name.title()} retrieval failed: {e}")
            return []

    def _search_store_with_scores(self, store_name: str, store: object, query: str, k: int) -> List[Tuple[Document, float]]:
        """Return (Document, score) pairs. Higher score = more relevant (cosine sim)."""
        if not store:
            return []
        try:
            if store_name == "sashwat_optimized":
                context = store.retrieve_context(query, k=k)
                if not context:
                    return []
                return [
                    (Document(page_content=context, metadata={"source": "sashwat_optimized_mmr"}), 1.0)
                ]

            if store_name == "optimized":
                retriever = store.as_retriever(similarity_top_k=k)
                nodes = retriever.retrieve(query)
                return [
                    (Document(page_content=node.text, metadata=node.metadata), node.score or 0.0)
                    for node in nodes
                ]

            # ChromaDB supports similarity_search_with_relevance_scores (cosine sim: higher = better)
            if hasattr(store, "similarity_search_with_relevance_scores"):
                results = store.similarity_search_with_relevance_scores(query, k=k)
                logger.info(f"{store_name.title()} DB: {len(results)} scored chunks.")
                return results

            # Fallback: use similarity_search without scores — assume moderate relevance
            docs = store.similarity_search(query, k=k)
            return [(doc, 0.45) for doc in docs]
        except Exception as e:
            logger.error(f"{store_name.title()} scored retrieval failed: {e}")
            return []

    def retrieve_context(self, query: str, k: int = 3, source: Optional[str] = "all") -> str:
        """
        Query the selected knowledge base(s) and combine results.
        Returns combined context string for downstream LLM prompts.
        """
        results: List[Document] = []
        enabled_stores = self._get_enabled_stores(source)
        if not enabled_stores:
            logger.warning(f"No RAG stores available for source='{source}'.")
            return ""

        for store_name, store in enabled_stores:
            results.extend(self._search_store(store_name, store, query, k))

        if not results:
            logger.warning("No results from any DB.")
            return ""

        context = "\n\n".join([doc.page_content for doc in results])
        logger.info(f"Total: {len(results)} chunks retrieved across all DBs.")
        return context

    def retrieve_context_with_scores(self, query: str, k: int = 3, source: Optional[str] = "all") -> Tuple[str, List[float]]:
        """
        Like retrieve_context but also returns per-document similarity scores.
        For ChromaDB stores these are cosine-similarity scores (higher = more relevant).
        Returns (combined_context, list_of_scores).
        """
        all_docs: List[Document] = []
        all_scores: List[float] = []
        enabled_stores = self._get_enabled_stores(source)
        if not enabled_stores:
            return ("", [])

        for store_name, store in enabled_stores:
            scored = self._search_store_with_scores(store_name, store, query, k)
            for doc, score in scored:
                all_docs.append(doc)
                all_scores.append(score)

        if not all_docs:
            return ("", [])

        context = "\n\n".join([doc.page_content for doc in all_docs])
        logger.info(f"Scored retrieval: {len(all_docs)} chunks, scores={[round(s,3) for s in all_scores]}")
        return (context, all_scores)

    def retrieve_structured(self, query: str, k: int = 3, source: Optional[str] = "all") -> dict:
        """
        Returns structured context from the selected DB(s) separately.
        Used by Geshna's question flow to get targeted results.
        """
        structured = {
            "sashwat_optimized": [],
            "optimized": [],
            "arohan":   [],
            "sashwat":  [],
            "harshita": [],
            "geshna":   [],
        }
        for store_name, store in self._get_enabled_stores(source):
            structured[store_name] = [
                doc.page_content for doc in self._search_store(store_name, store, query, k)
            ]

        return structured


def get_rag_context(query: str, k: int = 3, source: Optional[str] = "all") -> str:
    return rag_service.retrieve_context(query, k=k, source=source)


rag_service = RAGService()
