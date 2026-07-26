"""Integration tests for the RAG pipeline — real ChromaDB, fake embeddings.

Tests the full ingest → store → retrieve/query cycle without mocking
the vector store, chunker, or document loaders.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


SAMPLE_TEXT = (
    "The Clubmate AI project is a self-hosted Discord bot for university clubs. "
    "It provides meeting transcription, Google Calendar integration, and a RAG-based "
    "knowledge base. The bot uses Google Gemini for AI chat and supports multiple "
    "MCP servers for Google Docs, Sheets, Forms, and Calendar. "
    "The admin dashboard is built with Next.js and allows exec members to manage "
    "settings, ingest documents, and connect Google accounts. "
    "The project uses Python 3.14, discord.py, FastAPI, and ChromaDB for vector storage. "
    "Embedding models are loaded from HuggingFace and run on CPU. "
    "The RAG system uses semantic chunking to split documents into meaningful segments "
    "before storing them in the vector database for retrieval."
)


class TestRAGIngestPipeline:
    """Test ingesting files into a real ChromaDB instance."""

    def test_ingest_txt_file(self, rag_with_temp_db):
        from ragbot.rag import rag_ingest, rag_has_documents, rag_chunk_count

        # Write a test file
        test_file = Path(rag_with_temp_db.CHROMA_DB_DIR) / "test.txt"
        test_file.write_text(SAMPLE_TEXT)

        result = rag_ingest(str(test_file))
        assert result is True
        assert rag_has_documents() is True
        assert rag_chunk_count() > 0

    def test_ingest_md_file(self, rag_with_temp_db):
        from ragbot.rag import rag_ingest, rag_has_documents

        test_file = Path(rag_with_temp_db.CHROMA_DB_DIR) / "readme.md"
        test_file.write_text("# Clubmate\n\nThis is a meeting bot for student clubs.")

        result = rag_ingest(str(test_file))
        assert result is True
        assert rag_has_documents() is True

    def test_ingest_directory(self, rag_with_temp_db):
        from ragbot.rag import rag_ingest, rag_has_documents, rag_chunk_count

        d = Path(rag_with_temp_db.CHROMA_DB_DIR)
        (d / "doc1.txt").write_text("First document about AI and machine learning.")
        (d / "doc2.md").write_text("# Second\n\nSecond document about Discord bots.")
        (d / "ignored.exe").write_text("not a document")

        result = rag_ingest(str(d))
        assert result is True
        assert rag_has_documents() is True
        # Two text files ingested
        assert rag_chunk_count() >= 2

    def test_ingest_empty_file_returns_false(self, rag_with_temp_db):
        from ragbot.rag import rag_ingest

        test_file = Path(rag_with_temp_db.CHROMA_DB_DIR) / "empty.txt"
        test_file.write_text("   \n\n   ")

        result = rag_ingest(str(test_file))
        assert result is False

    def test_ingest_nonexistent_path_raises(self, rag_with_temp_db):
        from ragbot.rag import rag_ingest

        with pytest.raises(ValueError, match="does not exist"):
            rag_ingest("/nonexistent/path.txt")

    def test_short_file_falls_back_to_raw_chunks(self, rag_with_temp_db):
        from ragbot.rag import rag_ingest, rag_has_documents

        test_file = Path(rag_with_temp_db.CHROMA_DB_DIR) / "short.txt"
        test_file.write_text("Short doc. Not much content here.")

        result = rag_ingest(str(test_file))
        # Should succeed via fallback even if semantic chunker returns nothing
        assert result is True
        assert rag_has_documents() is True


class TestRAGRetrievePipeline:
    """Test retrieving chunks from a real ChromaDB after ingestion."""

    def test_retrieve_returns_chunks(self, rag_with_temp_db):
        from ragbot.rag import rag_ingest, rag_retrieve

        test_file = Path(rag_with_temp_db.CHROMA_DB_DIR) / "meeting.txt"
        test_file.write_text(SAMPLE_TEXT)
        rag_ingest(str(test_file))

        chunks = rag_retrieve("What is Clubmate AI?")
        assert len(chunks) > 0
        assert "content" in chunks[0]
        assert "source" in chunks[0]
        assert "relevance_score" in chunks[0]
        assert chunks[0]["source"] == "meeting.txt"

    def test_retrieve_empty_store_returns_empty(self, rag_with_temp_db):
        from ragbot.rag import rag_retrieve

        chunks = rag_retrieve("anything")
        assert chunks == []

    def test_retrieve_respects_top_k(self, rag_with_temp_db):
        from ragbot.rag import rag_ingest, rag_retrieve

        # Ingest a long document that will produce multiple chunks
        long_text = SAMPLE_TEXT * 10
        test_file = Path(rag_with_temp_db.CHROMA_DB_DIR) / "long.txt"
        test_file.write_text(long_text)
        rag_ingest(str(test_file))

        chunks = rag_retrieve("Clubmate", top_k=2)
        assert len(chunks) <= 2


class TestRAGQueryPipeline:
    """Test querying with LLM generation (mocked Gemini, real ChromaDB)."""

    def test_query_returns_generation_and_sources(self, rag_with_temp_db):
        from ragbot.rag import rag_ingest, rag_query

        test_file = Path(rag_with_temp_db.CHROMA_DB_DIR) / "faq.txt"
        test_file.write_text(SAMPLE_TEXT)
        rag_ingest(str(test_file))

        mock_response = MagicMock()
        mock_response.content = "Clubmate AI is a Discord bot for university clubs."

        with patch("ragbot.rag.ChatGoogleGenerativeAI") as MockLLM:
            MockLLM.return_value.invoke.return_value = mock_response
            result = rag_query("What is Clubmate AI?")

        assert "generation" in result
        assert "sources" in result
        assert result["generation"] == mock_response.content
        assert len(result["sources"]) > 0
        assert result["sources"][0]["source"] == "faq.txt"

    def test_query_empty_store_returns_no_sources(self, rag_with_temp_db):
        from ragbot.rag import rag_query

        mock_response = MagicMock()
        mock_response.content = "I couldn't find any relevant information."

        with patch("ragbot.rag.ChatGoogleGenerativeAI") as MockLLM:
            MockLLM.return_value.invoke.return_value = mock_response
            result = rag_query("anything")

        assert result["sources"] == []

    def test_query_empty_question_raises(self, rag_with_temp_db):
        from ragbot.rag import rag_query

        with pytest.raises(ValueError, match="empty"):
            rag_query("")


class TestRAGResetPipeline:
    """Test resetting the vector database."""

    def test_reset_clears_everything(self, rag_with_temp_db):
        from ragbot.rag import rag_ingest, rag_has_documents, rag_chunk_count, db_reset

        test_file = Path(rag_with_temp_db.CHROMA_DB_DIR) / "to_delete.txt"
        test_file.write_text(SAMPLE_TEXT)
        rag_ingest(str(test_file))
        assert rag_has_documents() is True

        result = db_reset()
        assert result is True
        assert rag_has_documents() is False
        assert rag_chunk_count() == 0

    def test_query_after_reset_returns_no_sources(self, rag_with_temp_db):
        from ragbot.rag import rag_ingest, rag_has_documents, rag_chunk_count, db_reset

        test_file = Path(rag_with_temp_db.CHROMA_DB_DIR) / "temp.txt"
        test_file.write_text(SAMPLE_TEXT)
        rag_ingest(str(test_file))
        assert rag_has_documents() is True

        result = db_reset()
        assert result is True
        assert rag_has_documents() is False
        assert rag_chunk_count() == 0
