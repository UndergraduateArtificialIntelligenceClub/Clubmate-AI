"""Configuration management using Pydantic settings."""

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""

    SENTENCE_TRANSFORMERS = "sentence-transformers"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

    # Pinecone Configuration
    pinecone_api_key: str = Field(..., description="Pinecone API key")
    pinecone_environment: str = Field(default="us-west1-gcp", description="Pinecone environment")
    pinecone_index_name: str = Field(default="rag-documents", description="Pinecone index name")

    # Google/Gemini Configuration
    google_api_key: str = Field(..., description="Google API key for Gemini")
    gemini_model: str = Field(default="gemini-1.5-pro", description="Gemini model to use")

    # Embedding Configuration
    embedding_model: EmbeddingProvider = Field(
        default=EmbeddingProvider.SENTENCE_TRANSFORMERS,
        description="Embedding provider to use"
    )
    sentence_transformer_model: str = Field(
        default="BAAI/bge-base-en-v1.5",
        description="Sentence transformer model name"
    )

    # RAG Parameters
    chunk_size: int = Field(default=1000, ge=100, le=10000, description="Target chunk size in characters")
    chunk_overlap: int = Field(default=200, ge=0, le=1000, description="Chunk overlap in characters")
    top_k_results: int = Field(default=5, ge=1, le=20, description="Number of top results to retrieve")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature for generation")

    # Application Settings
    log_level: str = Field(default="INFO", description="Logging level")
    data_dir: str = Field(default="./data", description="Data directory path")

    @field_validator('data_dir')
    @classmethod
    def validate_data_dir(cls, v: str) -> str:
        """Ensure data directory exists."""
        data_path = Path(v)
        data_path.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator('chunk_overlap')
    @classmethod
    def validate_chunk_overlap(cls, v: int, info) -> int:
        """Ensure chunk overlap is less than chunk size."""
        if 'chunk_size' in info.data and v >= info.data['chunk_size']:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return v

    def get_embedding_dimension(self) -> int:
        """Get the dimension of the configured embedding model."""
        # All common sentence-transformers models have known dimensions
        dimensions = {
            "BAAI/bge-base-en-v1.5": 768,
            "BAAI/bge-large-en-v1.5": 1024,
            "all-mpnet-base-v2": 768,
            "all-MiniLM-L6-v2": 384,
            "all-MiniLM-L12-v2": 384,
        }
        return dimensions.get(self.sentence_transformer_model, 768)

    def display_config(self) -> dict:
        """Return safe configuration for display (without API keys)."""
        return {
            "Pinecone Environment": self.pinecone_environment,
            "Pinecone Index": self.pinecone_index_name,
            "Gemini Model": self.gemini_model,
            "Embedding Provider": "sentence-transformers",
            "Embedding Model": self.sentence_transformer_model,
            "Embedding Dimension": self.get_embedding_dimension(),
            "Chunk Size": self.chunk_size,
            "Chunk Overlap": self.chunk_overlap,
            "Top-K Results": self.top_k_results,
            "Temperature": self.temperature,
            "Log Level": self.log_level,
            "Data Directory": self.data_dir,
        }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment (useful for testing)."""
    global _settings
    _settings = Settings()
    return _settings
