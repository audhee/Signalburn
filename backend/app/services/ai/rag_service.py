from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from app.knowledge_base.health_data import HEALTH_KNOWLEDGE_BASE
from app.knowledge_base.first_aid_data import FIRST_AID_DOCUMENTS
import logging

logger = logging.getLogger(__name__)

class RAGService:
    """
    RAG (Retrieval Augmented Generation) service for Arohan health assistant.
    Embeds the health knowledge base and retrieves relevant context for queries.
    """

    def __init__(self):
        self.db = None
        self.embedding_model = None
        self._initialize()

    def _initialize(self):
        """Load embedding model and build ChromaDB from health knowledge base."""
        try:
            logger.info("Initializing RAG service — loading embedding model...")

            self.embedding_model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )

            documents = [
                Document(
                    page_content=text,
                    metadata={"source": "arohan_health_kb"}
                )
                for text in HEALTH_KNOWLEDGE_BASE
            ]

            # Convert first aid records to LangChain Document objects
            first_aid_documents = [
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

            # Combine both knowledge bases
            documents = documents + first_aid_documents

            # Build ChromaDB vector store in memory
            self.db = Chroma.from_documents(
                documents,
                self.embedding_model,
                collection_name="arohan_health_knowledge"
            )

            logger.info(f"RAG service ready — {len(documents)} documents embedded.")

        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            # Gracefully degrade so the rest of the app (auth, etc.) still works
            self.embedding_model = None
            self.db = None

    def retrieve_context(self, query: str, k: int = 3) -> str:
        """
        Retrieve top-k relevant chunks for a given query.
        Returns them as a single joined context string for the LLM.
        """
        if not self.db:
            logger.warning("RAG DB not initialized, returning empty context.")
            return ""

        try:
            results = self.db.similarity_search(query, k=k)
            context = "\n\n".join([doc.page_content for doc in results])
            logger.info(f"Retrieved {len(results)} chunks for query: '{query[:50]}'")
            return context

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return ""


# Singleton instance — initialized once when server starts
rag_service = RAGService()