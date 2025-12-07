"""Tests for embedding modules."""

import pytest
from src.embeddings.sentence_transformer import SentenceTransformerEmbedder
from src.embeddings.base import EmbedderFactory


def test_sentence_transformer_embedder():
    """Test sentence-transformers embeddings."""
    embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")

    # Test single embedding
    text = "This is a test sentence."
    embedding = embedder.embed_query(text)

    assert isinstance(embedding, list)
    assert len(embedding) == 384  # all-MiniLM-L6-v2 dimension
    assert all(isinstance(x, float) for x in embedding)


def test_sentence_transformer_batch_embedding():
    """Test batch embedding with sentence-transformers."""
    embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")

    texts = [
        "First test sentence.",
        "Second test sentence.",
        "Third test sentence."
    ]

    embeddings = embedder.embed_documents(texts)

    assert len(embeddings) == 3
    assert all(len(emb) == 384 for emb in embeddings)
    assert all(isinstance(emb, list) for emb in embeddings)


def test_sentence_transformer_dimension():
    """Test dimension property."""
    embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
    assert embedder.dimension == 384


def test_embedder_factory_sentence_transformers():
    """Test factory creates sentence-transformers embedder."""
    embedder = EmbedderFactory.create_embedder(
        "sentence-transformers",
        model_name="all-MiniLM-L6-v2"
    )

    assert isinstance(embedder, SentenceTransformerEmbedder)
    assert embedder.dimension == 384


def test_embedder_factory_invalid_provider():
    """Test factory raises error for invalid provider."""
    with pytest.raises(ValueError, match="Unsupported embedding provider"):
        EmbedderFactory.create_embedder("invalid-provider")


def test_empty_text_handling():
    """Test handling of empty text."""
    embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")

    with pytest.raises(ValueError, match="Cannot embed empty text"):
        embedder.embed_query("")

    # Empty list should return empty list
    result = embedder.embed_documents([])
    assert result == []
