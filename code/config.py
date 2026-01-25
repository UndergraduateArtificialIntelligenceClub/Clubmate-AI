"""Configuration for RAG API."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file - check rag_api folder first, then parent
rag_api_env = Path(__file__).parent / '.env'
parent_env = Path(__file__).parent.parent / '.env'

if rag_api_env.exists():
    load_dotenv(rag_api_env)
elif parent_env.exists():
    load_dotenv(parent_env)


class RAGConfig:
    """Configuration settings for RAG API."""
    
    # ChromaDB settings
    CHROMA_DB_DIR: str = os.getenv("CHROMA_DB_DIR", "./chroma_db")
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "rag-documents")
    
    # Embedding settings
    EMBEDDING_MODEL: str = os.getenv("SENTENCE_TRANSFORMER_MODEL", "BAAI/bge-base-en-v1.5")
    EMBEDDING_DIMENSION: int = 768  # for BAAI/bge-base-en-v1.5
    
    # Google API
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    DEFAULT_LLM_MODEL: str = "gemini-2.0-flash-exp"
    
    # RAG parameters
    TOP_K_RESULTS: int = 5
    TEMPERATURE: float = 0.7
    CHUNK_THRESHOLD_TYPE: str = "percentile"
    CHUNK_THRESHOLD_AMOUNT: float = 95.0
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is required. "
                "Set it in .env or export it."
            )
        
        # Ensure ChromaDB directory exists
        Path(cls.CHROMA_DB_DIR).mkdir(parents=True, exist_ok=True)
