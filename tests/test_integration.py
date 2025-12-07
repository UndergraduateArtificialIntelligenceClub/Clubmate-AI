"""Integration tests for the RAG system.

Note: These tests are marked as integration and should be run with actual API keys configured.
They can be skipped in CI/CD pipelines.
"""

import pytest
from pathlib import Path

from src.document_loaders.file_ingestion import FileIngestionLoader
from src.embeddings.sentence_transformer import SentenceTransformerEmbedder
from src.chunking.semantic_chunker import DocumentChunker


@pytest.mark.integration
def test_document_loading_and_chunking():
    """Test full workflow: load → chunk."""
    # Load test document
    fixture_path = Path(__file__).parent / "fixtures" / "sample.txt"
    loader = FileIngestionLoader(str(fixture_path))
    documents = loader.load()

    assert len(documents) > 0

    # Create embeddings and chunker
    embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
    chunker = DocumentChunker(embeddings=embedder)

    # Chunk documents
    chunks = chunker.chunk_documents(documents)

    # Verify chunks were created
    assert len(chunks) > 0

    # Verify metadata is preserved
    for chunk in chunks:
        assert "source" in chunk.metadata
        assert "chunk_index" in chunk.metadata
        assert "total_chunks" in chunk.metadata
        assert "chunk_method" in chunk.metadata
        assert chunk.metadata["chunk_method"] == "semantic"


@pytest.mark.integration
def test_markdown_loading_and_chunking():
    """Test markdown document loading and chunking."""
    # Load markdown document
    fixture_path = Path(__file__).parent / "fixtures" / "sample.md"

    loader = FileIngestionLoader(str(fixture_path))
    documents = loader.load()

    assert len(documents) > 0
    assert documents[0].metadata["document_type"] == "markdown"

    # Chunk the markdown
    embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
    chunker = DocumentChunker(embeddings=embedder)
    chunks = chunker.chunk_documents(documents)

    assert len(chunks) > 0

    # Verify original metadata is preserved
    for chunk in chunks:
        assert chunk.metadata["document_type"] == "markdown"


@pytest.mark.integration
def test_chunk_text_utility():
    """Test chunking raw text."""
    embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
    chunker = DocumentChunker(embeddings=embedder)

    text = """
    This is a long text that should be chunked into multiple pieces.
    It contains several sentences that will be semantically analyzed.
    The chunker should create logical breaks based on semantic similarity.
    This helps maintain context in each chunk for better retrieval.
    """

    chunks = chunker.chunk_text(text, metadata={"source": "test"})

    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.metadata["source"] == "test"
        assert "chunk_index" in chunk.metadata
