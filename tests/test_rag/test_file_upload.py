"""Tests for ragbot/sources/file_upload.py"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ragbot.sources.file_upload import ingest_uploaded_file, SUPPORTED_EXTENSIONS


class TestSupportedExtensions:
    def test_has_expected_types(self):
        assert ".pdf" in SUPPORTED_EXTENSIONS
        assert ".txt" in SUPPORTED_EXTENSIONS
        assert ".md" in SUPPORTED_EXTENSIONS
        assert ".markdown" in SUPPORTED_EXTENSIONS

    def test_no_exe(self):
        assert ".exe" not in SUPPORTED_EXTENSIONS


class TestIngestUploadedFile:
    def test_unsupported_extension_raises(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            ingest_uploaded_file("test.exe", b"binary content")

    def test_txt_file_calls_rag_ingest(self):
        with patch("ragbot.rag.rag_ingest", return_value=True) as mock_ingest:
            result = ingest_uploaded_file("notes.txt", b"Hello world")
        assert result is True
        mock_ingest.assert_called_once()
        call_arg = mock_ingest.call_args[0][0]
        assert isinstance(call_arg, str)
        assert call_arg.endswith(".txt")

    def test_md_file_calls_rag_ingest(self):
        with patch("ragbot.rag.rag_ingest", return_value=True) as mock_ingest:
            result = ingest_uploaded_file("readme.md", b"# Title")
        assert result is True

    def test_cleans_up_temp_file(self):
        captured_paths = []

        def fake_ingest(path):
            captured_paths.append(path)
            assert Path(path).exists(), "Temp file should exist during ingest"
            return True

        with patch("ragbot.rag.rag_ingest", side_effect=fake_ingest):
            ingest_uploaded_file("temp.txt", b"content")

        assert len(captured_paths) == 1
        assert not Path(captured_paths[0]).exists(), "Temp file should be cleaned up"

    def test_propagates_rag_ingest_failure(self):
        with patch("ragbot.rag.rag_ingest", return_value=False):
            result = ingest_uploaded_file("empty.txt", b"nothing useful")
        assert result is False

    def test_no_filename_raises(self):
        with pytest.raises(TypeError):
            ingest_uploaded_file(None, b"content")

    def test_empty_suffix_raises(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            ingest_uploaded_file("noextension", b"content")
