"""Configuration for RAG API."""

import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env file from project root
_project_root = Path(__file__).parent.parent
_env_file = _project_root / '.env'

if _env_file.exists():
    load_dotenv(_env_file)
    # Using info level for consistent condensed logging
    logger.info(f"Config loaded from {_env_file.name}")
else:
    logger.warning(
        f"No .env file found at {_env_file}. "
        "Please copy .env.example to .env and configure it. "
        "Falling back to environment variables."
    )


class RAGConfig:
    """Configuration settings for RAG API."""
    
    # ChromaDB settings
    CHROMA_DB_DIR: str = os.getenv("CHROMA_DB_DIR", str(Path(__file__).parent / "chroma_db"))
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "rag-documents")
    
    # Embedding settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
    EMBEDDING_DIMENSION: int = 768  # for BAAI/bge-base-en-v1.5
    
    # Gemini API
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "gemini-2.5-flash-lite")
    
    # RAG parameters
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "5"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    CHUNK_THRESHOLD_TYPE: str = os.getenv("CHUNK_THRESHOLD_TYPE", "percentile")
    CHUNK_THRESHOLD_AMOUNT: float = float(os.getenv("CHUNK_THRESHOLD_AMOUNT", "95.0"))
    
    # Track if .env was loaded
    _env_loaded: bool = _env_file.exists()
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate required configuration.
        
        Raises:
            FileNotFoundError: If .env file is missing
            ValueError: If required configuration values are not set
        """
        errors = []
        
        # Check if .env file exists
        if not cls._env_loaded:
            errors.append(
                f"Configuration file not found: {_env_file}\n"
                f"  → Copy .env.example to .env: cp {_project_root}/.env.example {_env_file}"
            )
        
        # Check required configurations
        if not cls.GEMINI_API_KEY:
            errors.append(
                "GEMINI_API_KEY is not set.\n"
                "  → Get your API key from: https://makersuite.google.com/app/apikey\n"
                "  → Add to .env: GEMINI_API_KEY=your-api-key-here"
            )
        
        # Raise all errors at once for better UX
        if errors:
            error_msg = "RAG Configuration Error(s):\n\n" + "\n\n".join(f"❌ {e}" for e in errors)
            raise ValueError(error_msg)
        
        # Ensure ChromaDB directory exists
        Path(cls.CHROMA_DB_DIR).mkdir(parents=True, exist_ok=True)
        logger.info("✅ RAG config validated")
    
    @classmethod
    def is_configured(cls) -> bool:
        """
        Check if RAG is properly configured without raising exceptions.
        
        Returns:
            True if all required configuration is present, False otherwise
        """
        return cls._env_loaded and bool(cls.GEMINI_API_KEY)
    
    @classmethod
    def get_status(cls) -> dict:
        """
        Get configuration status for debugging.
        
        Returns:
            Dictionary with configuration status
        """
        return {
            "env_file_loaded": cls._env_loaded,
            "env_file_path": str(_env_file),
            "gemini_api_key_set": bool(cls.GEMINI_API_KEY),
            "chroma_db_dir": cls.CHROMA_DB_DIR,
            "embedding_model": cls.EMBEDDING_MODEL,
            "default_llm_model": cls.DEFAULT_LLM_MODEL,
            "top_k_results": cls.TOP_K_RESULTS,
        }
