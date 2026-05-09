import os
import logging
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

    def retrieve_context(self, query: str, k: int = 3) -> str:
        """
        Query all 4 DBs and combine results.
        Returns combined context string for Gemini.
        """
        results = []

        # 1. Arohan KB
        if self.arohan_db:
            try:
                res = self.arohan_db.similarity_search(query, k=k)
                results.extend(res)
                logger.info(f"Arohan KB: {len(res)} chunks.")
            except Exception as e:
                logger.error(f"Arohan KB retrieval failed: {e}")

        # 2. Sashwat medical DB
        if self.sashwat_db:
            try:
                res = self.sashwat_db.similarity_search(query, k=k)
                results.extend(res)
                logger.info(f"Sashwat DB: {len(res)} chunks.")
            except Exception as e:
                logger.error(f"Sashwat DB retrieval failed: {e}")

        # 3. Harshita FAISS
        if self.harshita_db:
            try:
                res = self.harshita_db.similarity_search(query, k=k)
                results.extend(res)
                logger.info(f"Harshita FAISS: {len(res)} chunks.")
            except Exception as e:
                logger.error(f"Harshita FAISS retrieval failed: {e}")

        # 4. Geshna FAISS
        if self.geshna_db:
            try:
                res = self.geshna_db.similarity_search(query, k=k)
                results.extend(res)
                logger.info(f"Geshna FAISS: {len(res)} chunks.")
            except Exception as e:
                logger.error(f"Geshna FAISS retrieval failed: {e}")

        if not results:
            logger.warning("No results from any DB.")
            return ""

        context = "\n\n".join([doc.page_content for doc in results])
        logger.info(f"Total: {len(results)} chunks retrieved across all DBs.")
        return context

    def retrieve_structured(self, query: str, k: int = 3) -> dict:
        """
        Returns structured context from each DB separately.
        Used by Geshna's question flow to get targeted results.
        """
        structured = {
            "arohan":   [],
            "sashwat":  [],
            "harshita": [],
            "geshna":   [],
        }

        if self.arohan_db:
            try:
                structured["arohan"] = [
                    d.page_content for d in self.arohan_db.similarity_search(query, k=k)
                ]
            except Exception as e:
                logger.error(f"Arohan structured retrieval failed: {e}")

        if self.sashwat_db:
            try:
                structured["sashwat"] = [
                    d.page_content for d in self.sashwat_db.similarity_search(query, k=k)
                ]
            except Exception as e:
                logger.error(f"Sashwat structured retrieval failed: {e}")

        if self.harshita_db:
            try:
                structured["harshita"] = [
                    d.page_content for d in self.harshita_db.similarity_search(query, k=k)
                ]
            except Exception as e:
                logger.error(f"Harshita structured retrieval failed: {e}")

        if self.geshna_db:
            try:
                structured["geshna"] = [
                    d.page_content for d in self.geshna_db.similarity_search(query, k=k)
                ]
            except Exception as e:
                logger.error(f"Geshna structured retrieval failed: {e}")

        return structured


rag_service = RAGService()