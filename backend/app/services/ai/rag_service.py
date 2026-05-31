from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from app.knowledge_base.health_data import HEALTH_KNOWLEDGE_BASE
from app.knowledge_base.first_aid_data import FIRST_AID_DOCUMENTS
import logging
import os

logger = logging.getLogger(__name__)

SASHWAT_CHROMA_DIR = r"D:\intern\medical-rag-llm\db\my_chroma_db"

class RAGService:
    def __init__(self):
        self.db              = None
        self.sashwat_db      = None
        self.embedding_model = None
        self._initialize()

    def _initialize(self):
        try:
            logger.info("Initializing RAG service...")

            self.embedding_model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )

            health_docs = [
                Document(
                    page_content=text,
                    metadata={"source": "arohan_health_kb"}
                )
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

            all_docs = health_docs + first_aid_docs

            self.db = Chroma.from_documents(
                all_docs,
                self.embedding_model,
                collection_name="arohan_health_knowledge"
            )

            logger.info(f"Arohan KB ready — {len(all_docs)} documents embedded.")

            if os.path.exists(SASHWAT_CHROMA_DIR):
                self.sashwat_db = Chroma(
                    persist_directory=SASHWAT_CHROMA_DIR,
                    embedding_function=self.embedding_model,
                )
                logger.info("Sashwat medical DB loaded successfully.")
            else:
                logger.warning(f"Sashwat DB not found at {SASHWAT_CHROMA_DIR}")

        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise

    def retrieve_context(self, query: str, k: int = 5) -> str:
        """
        Retrieves top-k chunks from both DBs.
        Each chunk trimmed to 300 chars, total max 2000 chars.
        """
        results = []

        if self.db:
            try:
                arohan_results = self.db.similarity_search(query, k=k)
                results.extend(arohan_results)
                logger.info(f"Arohan KB: {len(arohan_results)} chunks retrieved")
            except Exception as e:
                logger.error(f"Arohan KB retrieval failed: {e}")

        if self.sashwat_db:
            try:
                sashwat_results = self.sashwat_db.similarity_search(query, k=k)
                results.extend(sashwat_results)
                logger.info(f"Sashwat DB: {len(sashwat_results)} chunks retrieved")
            except Exception as e:
                logger.error(f"Sashwat DB retrieval failed: {e}")

        if not results:
            logger.warning("No results from either DB")
            return ""

        # Trim each chunk to 300 chars — enough info, not too long
        trimmed = [doc.page_content[:300] for doc in results]
        context = "\n\n".join(trimmed)
        # Total max 2000 chars for LLM
        context = context[:2000]

        logger.info(f"Total {len(results)} chunks, {len(context)} chars combined")
        return context


def get_rag_context(query: str) -> str:
    return rag_service.retrieve_context(query)


rag_service = RAGService()