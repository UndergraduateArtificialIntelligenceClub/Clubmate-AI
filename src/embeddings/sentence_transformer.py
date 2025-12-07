"""Sentence Transformers embedding implementation."""

from typing import List
import logging

from .base import BaseEmbedder

logger = logging.getLogger(__name__)


class SentenceTransformerEmbedder(BaseEmbedder):
    """Embedder using local sentence-transformers models."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", batch_size: int = 32):
        """
        Initialize SentenceTransformer embedder.

        Args:
            model_name: Name of the sentence-transformers model to use
            batch_size: Batch size for encoding (default: 32)
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: uv pip install sentence-transformers"
            )

        self.model_name = model_name
        self.batch_size = batch_size

        logger.info(f"Loading sentence-transformers model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self._dimension}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents using sentence-transformers.

        Args:
            texts: List of document texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Remove empty texts
        texts = [text.strip() for text in texts if text.strip()]

        if not texts:
            return []

        # Encode in batches for efficiency
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        # Convert numpy arrays to lists of floats
        return [embedding.tolist() for embedding in embeddings]

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query using sentence-transformers.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        if not text.strip():
            raise ValueError("Cannot embed empty text")

        embedding = self.model.encode(
            text,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        return embedding.tolist()

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._dimension
