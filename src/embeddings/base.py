"""Base embedding interface."""

from abc import ABC, abstractmethod
from typing import List

from langchain.embeddings.base import Embeddings


class BaseEmbedder(Embeddings, ABC):
    """
    Abstract base class for embedding generators.

    Inherits from LangChain's Embeddings for compatibility.
    """

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (each vector is a list of floats)
        """
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector as list of floats
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of embeddings produced by this embedder."""
        pass


class EmbedderFactory:
    """Factory for creating embedding instances based on configuration."""

    @staticmethod
    def create_embedder(provider: str, **kwargs) -> BaseEmbedder:
        """
        Create embedder instance based on provider name.

        Args:
            provider: Must be 'sentence-transformers'
            **kwargs: Additional arguments for the embedder

        Returns:
            BaseEmbedder instance

        Raises:
            ValueError: If provider is not supported
        """
        from .sentence_transformer import SentenceTransformerEmbedder

        provider = provider.lower()

        if provider == "sentence-transformers":
            return SentenceTransformerEmbedder(**kwargs)
        else:
            raise ValueError(
                f"Unsupported embedding provider: {provider}. "
                "Only 'sentence-transformers' is supported."
            )
