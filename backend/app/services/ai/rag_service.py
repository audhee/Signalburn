import os
import logging
from typing import Dict, List, Optional, Tuple
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain_core.documents import Document
from app.knowledge_base.health_data import HEALTH_KNOWLEDGE_BASE
from app.knowledge_base.first_aid_data import FIRST_AID_DOCUMENTS

logger = logging.getLogger(__name__)

# Paths to all databases
SASHWAT_CHROMA_DIR  = r"D:\intern\medical-rag-llm\db\my_chroma_db"
HARSHITA_FAISS_DIR  = r"D:\intern\Arohan\backend\app\knowledge_base\harshita_faiss_index"
GESHNA_FAISS_DIR    = r"D:\intern\Arohan\backend\app\knowledge_base\geshna_faiss"
VALID_RAG_SOURCES   = ("all", "arohan", "sashwat", "harshita", "geshna")


class RAGService:
    def __init__(self):
        self.arohan_db   = None   # in-memory ChromaDB (health + first aid)
        self.sashwat_db  = None   # Sashwat's medical ChromaDB
        self.harshita_db = None   # Harshita's FAISS (dynamic structured)
        self.geshna_db   = None   # Geshna's FAISS (question-flow based)
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

            # --- 1. Arohan in-memory KB ---
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

            # --- 2. Sashwat's ChromaDB ---
            if os.path.exists(SASHWAT_CHROMA_DIR):
                self.sashwat_db = Chroma(
                    persist_directory=SASHWAT_CHROMA_DIR,
                    embedding_function=self.embedding_model,
                )
                logger.info("Sashwat medical RAG DB loaded.")
            else:
                logger.warning(f"Sashwat DB not found at {SASHWAT_CHROMA_DIR}")

            # --- 3. Harshita's FAISS ---
            if os.path.exists(HARSHITA_FAISS_DIR):
                self.harshita_db = FAISS.load_local(
                    HARSHITA_FAISS_DIR,
                    self.embedding_model,
                    allow_dangerous_deserialization=True
                )
                logger.info("Harshita FAISS DB loaded.")
            else:
                logger.warning(f"Harshita FAISS not found at {HARSHITA_FAISS_DIR}")

            # --- 4. Geshna's FAISS ---
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

    def _normalize_source(self, source: Optional[str]) -> str:
        normalized = (source or "all").strip().lower()
        if normalized not in VALID_RAG_SOURCES:
            logger.warning(f"Unknown rag_source '{source}', defaulting to 'all'.")
            return "all"
        return normalized

    def _get_enabled_stores(self, source: Optional[str]) -> List[Tuple[str, object]]:
        normalized = self._normalize_source(source)
        stores: Dict[str, object] = {
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
            results = store.similarity_search(query, k=k)
            logger.info(f"{store_name.title()} DB: {len(results)} chunks.")
            return results
        except Exception as e:
            logger.error(f"{store_name.title()} retrieval failed: {e}")
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

    def retrieve_structured(self, query: str, k: int = 3, source: Optional[str] = "all") -> dict:
        """
        Returns structured context from the selected DB(s) separately.
        Used by Geshna's question flow to get targeted results.
        """
        structured = {
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
