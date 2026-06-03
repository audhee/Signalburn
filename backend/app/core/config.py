import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Explicitly load .env from project root FIRST, then backend directory (reliable on Windows)
# Project root has real API keys, backend/.env has overrides if needed
_env_paths = [
    Path(__file__).parent.parent.parent.parent / '.env', # project root (./.env)
    Path(__file__).parent.parent.parent / '.env',      # backend/.env
]
loaded = False
for _env_path in _env_paths:
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path)
        loaded = True
if not loaded:
    # Fallback: search upward from CWD
    load_dotenv(find_dotenv(usecwd=True))


class Settings:
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey123456789abcdefghij")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Local Model Configuration (Dual Mode)
    USE_LOCAL_MODEL: bool = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "arohan-medical")

    # RAG Configuration
    SASHWAT_CHROMA_DIR: str = os.getenv(
        "SASHWAT_CHROMA_DIR",
        r"D:\intern\medical-rag-llm\db\my_chroma_db",
    )
    HARSHITA_FAISS_DIR: str = os.getenv(
        "HARSHITA_FAISS_DIR",
        str(Path(__file__).parent.parent / "knowledge_base" / "harshita_faiss_index"),
    )
    GESHNA_FAISS_DIR: str = os.getenv(
        "GESHNA_FAISS_DIR",
        str(Path(__file__).parent.parent / "knowledge_base" / "geshna_faiss"),
    )
    GUIDED_RAG_SOURCE: str = os.getenv("GUIDED_RAG_SOURCE", "sashwat_optimized")


settings = Settings()
