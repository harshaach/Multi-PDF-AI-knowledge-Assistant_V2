import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Centralized application configuration.
    """

    # ==========================
    # Gemini
    # ==========================
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    # ==========================
    # Embedding Model
    # ==========================
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    # ==========================
    # Semantic Chunking
    # ==========================
    TARGET_CHUNK_SIZE = 1500
    OVERLAP_SENTENCES = 2

    # ==========================
    # Retrieval
    # ==========================
    DEFAULT_TOP_K = 5
    MAX_TOP_K = 20
    SIMILARITY_THRESHOLD = 0.30
    # ==========================
    # Gemini
    # ==========================
    GEMINI_MODEL = "gemini-2.5-flash"

    # ==========================
    # Upload Directory
    # ==========================
    UPLOAD_DIR = Path("uploads")
    UPLOAD_DIR.mkdir(exist_ok=True)


settings = Settings()