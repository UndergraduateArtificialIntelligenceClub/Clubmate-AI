"""Tests for ragbot.rag — RAGSystem and module-level functions."""

import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


@pytest.fixture(autouse=True)
def reset_rag_singleton():
    """Reset RAGSystem singleton between tests."""
    from ragbot.rag import RAGSystem
    RAGSystem._instance = None
    RAGSystem._initialized = False
    yield
    RAGSystem._instance = None
    RAGSystem._initialized = False


class TestRAGConfig:
    def test_validate_raises_without_api_key(self):
        from ragbot.rag import RAGConfig
        original = RAGConfig.GEMINI_API_KEY
        try:
            RAGConfig.GEMINI_API_KEY = ""
            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                RAGConfig.validate()
        finally:
            RAGConfig.GEMINI_API_KEY = original

    def test_validate_creates_db_dir(self, tmp_path):
        from ragbot.rag import RAGConfig
        original_dir = RAGConfig.CHROMA_DB_DIR
        test_dir = str(tmp_path / "test_chroma")
        try:
            RAGConfig.CHROMA_DB_DIR = test_dir
            RAGConfig.GEMINI_API_KEY = "test-key"
            RAGConfig.validate()
            assert Path(test_dir).exists()
        finally:
            RAGConfig.CHROMA_DB_DIR = original_dir


class TestRAGSystemInit:
    @patch("ragbot.rag.Chroma")
    @patch("ragbot.rag.SemanticChunker")
    @patch("ragbot.rag.create_embeddings")
    @patch("ragbot.rag.RAGConfig.validate")
    def test_singleton_pattern(self, mock_validate, mock_embeddings, mock_chunker, mock_chroma):
        from ragbot.rag import RAGSystem
        mock_embeddings.return_value = MagicMock()
        mock_chunker.return_value = MagicMock()
        mock_chroma.return_value = MagicMock()

        r1 = RAGSystem()
        r2 = RAGSystem()
        assert r1 is r2

    @patch("ragbot.rag.Chroma")
    @patch("ragbot.rag.SemanticChunker")
    @patch("ragbot.rag.create_embeddings")
    @patch("ragbot.rag.RAGConfig.validate")
    def test_init_sets_initialized(self, mock_validate, mock_embeddings, mock_chunker, mock_chroma):
        from ragbot.rag import RAGSystem
        mock_embeddings.return_value = MagicMock()
        mock_chunker.return_value = MagicMock()
        mock_chroma.return_value = MagicMock()

        rag = RAGSystem()
        assert rag._initialized is True


class TestLoadDocument:
    @patch("ragbot.rag.Chroma")
    @patch("ragbot.rag.SemanticChunker")
    @patch("ragbot.rag.create_embeddings")
    @patch("ragbot.rag.RAGConfig.validate")
    def test_load_txt_file(self, mock_validate, mock_embeddings, mock_chunker, mock_chroma, tmp_path):
        from ragbot.rag import RAGSystem
        mock_embeddings.return_value = MagicMock()
        mock_chunker.return_value = MagicMock()
        mock_chroma.return_value = MagicMock()

        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello world")

        rag = RAGSystem()
        docs = rag.load_document(str(txt_file))
        assert len(docs) >= 1
        assert docs[0].metadata["source"] == "test.txt"

    @patch("ragbot.rag.Chroma")
    @patch("ragbot.rag.SemanticChunker")
    @patch("ragbot.rag.create_embeddings")
    @patch("ragbot.rag.RAGConfig.validate")
    def test_load_nonexistent_file_raises(self, mock_validate, mock_embeddings, mock_chunker, mock_chroma):
        from ragbot.rag import RAGSystem
        mock_embeddings.return_value = MagicMock()
        mock_chunker.return_value = MagicMock()
        mock_chroma.return_value = MagicMock()

        rag = RAGSystem()
        with pytest.raises(FileNotFoundError):
            rag.load_document("/nonexistent/file.txt")

    @patch("ragbot.rag.Chroma")
    @patch("ragbot.rag.SemanticChunker")
    @patch("ragbot.rag.create_embeddings")
    @patch("ragbot.rag.RAGConfig.validate")
    def test_load_unsupported_extension(self, mock_validate, mock_embeddings, mock_chunker, mock_chroma, tmp_path):
        from ragbot.rag import RAGSystem
        mock_embeddings.return_value = MagicMock()
        mock_chunker.return_value = MagicMock()
        mock_chroma.return_value = MagicMock()

        bad_file = tmp_path / "test.xyz"
        bad_file.write_text("data")

        rag = RAGSystem()
        with pytest.raises(ValueError, match="Unsupported file type"):
            rag.load_document(str(bad_file))


class TestIngestFile:
    @patch("ragbot.rag.Chroma")
    @patch("ragbot.rag.SemanticChunker")
    @patch("ragbot.rag.create_embeddings")
    @patch("ragbot.rag.RAGConfig.validate")
    def test_ingest_success(self, mock_validate, mock_embeddings, mock_chunker, mock_chroma, tmp_path):
        from ragbot.rag import RAGSystem, LCDocument
        mock_embeddings.return_value = MagicMock()
        mock_vector_store = MagicMock()
        mock_chroma.return_value = mock_vector_store

        chunker_instance = MagicMock()
        doc = LCDocument(page_content="test content", metadata={"source": "test.txt"})
        chunker_instance.split_documents.return_value = [doc]
        mock_chunker.return_value = chunker_instance

        txt_file = tmp_path / "test.txt"
        txt_file.write_text("test content")

        rag = RAGSystem()
        rag.vector_store = mock_vector_store
        result = rag.ingest_file(str(txt_file))
        assert result is True
        mock_vector_store.add_texts.assert_called_once()

    @patch("ragbot.rag.Chroma")
    @patch("ragbot.rag.SemanticChunker")
    @patch("ragbot.rag.create_embeddings")
    @patch("ragbot.rag.RAGConfig.validate")
    def test_ingest_empty_chunks_fallback_also_empty(self, mock_validate, mock_embeddings, mock_chunker, mock_chroma):
        from ragbot.rag import RAGSystem, LCDocument
        mock_embeddings.return_value = MagicMock()
        mock_vector_store = MagicMock()
        mock_chroma.return_value = mock_vector_store

        # Chunker returns empty, and raw docs have empty content -> should return False
        chunker_instance = MagicMock()
        chunker_instance.split_documents.return_value = []
        mock_chunker.return_value = chunker_instance

        rag = RAGSystem()
        rag.vector_store = mock_vector_store

        # Mock load_document to return doc with empty content
        empty_doc = LCDocument(page_content="   ", metadata={"source": "test.txt"})
        with patch.object(rag, "load_document", return_value=[empty_doc]):
            result = rag.ingest_file("/fake/test.txt")
            assert result is False


class TestQuery:
    @patch("ragbot.rag.ChatGoogleGenerativeAI")
    @patch("ragbot.rag.Chroma")
    @patch("ragbot.rag.SemanticChunker")
    @patch("ragbot.rag.create_embeddings")
    @patch("ragbot.rag.RAGConfig.validate")
    def test_query_empty_question_raises(self, mock_validate, mock_embeddings, mock_chunker, mock_chroma, mock_llm):
        from ragbot.rag import RAGSystem
        mock_embeddings.return_value = MagicMock()
        mock_chunker.return_value = MagicMock()
        mock_chroma.return_value = MagicMock()

        rag = RAGSystem()
        with pytest.raises(ValueError, match="Question cannot be empty"):
            rag.query("")

    @patch("ragbot.rag.ChatGoogleGenerativeAI")
    @patch("ragbot.rag.Chroma")
    @patch("ragbot.rag.SemanticChunker")
    @patch("ragbot.rag.create_embeddings")
    @patch("ragbot.rag.RAGConfig.validate")
    def test_query_no_results(self, mock_validate, mock_embeddings, mock_chunker, mock_chroma, mock_llm):
        from ragbot.rag import RAGSystem, LCDocument
        mock_embeddings.return_value = MagicMock()
        mock_vector_store = MagicMock()
        mock_vector_store.similarity_search_with_score.return_value = []
        mock_chroma.return_value = mock_vector_store
        mock_chunker.return_value = MagicMock()

        rag = RAGSystem()
        rag.vector_store = mock_vector_store
        result = rag.query("What is this?")
        assert "couldn't find" in result["generation"]
        assert result["sources"] == []


class TestReset:
    @patch("ragbot.rag.Chroma")
    @patch("ragbot.rag.SemanticChunker")
    @patch("ragbot.rag.create_embeddings")
    @patch("ragbot.rag.RAGConfig.validate")
    def test_reset_removes_directory(self, mock_validate, mock_embeddings, mock_chunker, mock_chroma, tmp_path):
        from ragbot.rag import RAGSystem, RAGConfig
        mock_embeddings.return_value = MagicMock()
        mock_chunker.return_value = MagicMock()
        mock_vector_store = MagicMock()
        mock_chroma.return_value = mock_vector_store

        test_db = tmp_path / "chroma_test"
        test_db.mkdir()
        (test_db / "file.txt").write_text("data")

        original_dir = RAGConfig.CHROMA_DB_DIR
        try:
            RAGConfig.CHROMA_DB_DIR = str(test_db)
            rag = RAGSystem()
            rag.vector_store = mock_vector_store
            result = rag.reset()
            assert result is True
            assert test_db.exists()
        finally:
            RAGConfig.CHROMA_DB_DIR = original_dir


class TestModuleFunctions:
    @patch("ragbot.rag._get_rag")
    def test_rag_ingest_calls_file(self, mock_get_rag, tmp_path):
        from ragbot.rag import rag_ingest
        rag = MagicMock()
        rag.ingest_file.return_value = True
        mock_get_rag.return_value = rag

        txt = tmp_path / "test.txt"
        txt.write_text("content")
        result = rag_ingest(str(txt))
        assert result is True
        rag.ingest_file.assert_called_once()

    @patch("ragbot.rag._get_rag")
    def test_rag_ingest_calls_directory(self, mock_get_rag, tmp_path):
        from ragbot.rag import rag_ingest
        rag = MagicMock()
        rag.ingest_directory.return_value = True
        mock_get_rag.return_value = rag

        result = rag_ingest(str(tmp_path))
        assert result is True
        rag.ingest_directory.assert_called_once()

    def test_rag_ingest_invalid_path(self):
        from ragbot.rag import rag_ingest
        with pytest.raises(ValueError, match="does not exist"):
            rag_ingest("/nonexistent/path/xyz")

    @patch("ragbot.rag._get_rag")
    def test_rag_query_calls_rag(self, mock_get_rag):
        from ragbot.rag import rag_query
        rag = MagicMock()
        rag.query.return_value = {"generation": "answer", "sources": []}
        mock_get_rag.return_value = rag

        result = rag_query("What is X?")
        assert result["generation"] == "answer"

    @patch("ragbot.rag._get_rag")
    def test_db_reset_calls_rag(self, mock_get_rag):
        from ragbot.rag import db_reset
        rag = MagicMock()
        rag.reset.return_value = True
        mock_get_rag.return_value = rag

        assert db_reset() is True
        rag.reset.assert_called_once()

    @patch("chromadb.PersistentClient")
    def test_rag_has_documents_false_when_no_sqlite(self, mock_persistent_client):
        from ragbot.rag import rag_has_documents, RAGConfig
        import os

        # Make sqlite path not exist
        original_dir = RAGConfig.CHROMA_DB_DIR
        test_dir = "/tmp/test_rag_no_sqlite"
        RAGConfig.CHROMA_DB_DIR = test_dir

        try:
            with patch("ragbot.rag.Path") as mock_path:
                mock_sqlite = MagicMock()
                mock_sqlite.exists.return_value = False
                mock_chroma_path = MagicMock()
                mock_chroma_path.__truediv__ = MagicMock(return_value=mock_sqlite)
                mock_path.return_value = mock_chroma_path

                result = rag_has_documents()
                assert result is False
        finally:
            RAGConfig.CHROMA_DB_DIR = original_dir
