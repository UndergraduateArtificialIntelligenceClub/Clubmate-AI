"""Tests for the unified file ingestion loader."""

from pathlib import Path

import pytest

from src.document_loaders.file_ingestion import FileIngestionLoader


def test_text_loader():
    """Load a UTF-8 text file."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample.txt"

    loader = FileIngestionLoader(str(fixture_path))
    documents = loader.load()

    assert len(documents) == 1
    assert "sample text file" in documents[0].page_content.lower()
    assert documents[0].metadata["document_type"] == "text"
    assert documents[0].metadata["source"] == "sample.txt"
    assert documents[0].metadata["file_path"].endswith("sample.txt")
    assert documents[0].metadata["encoding"] == "utf-8"


def test_markdown_loader():
    """Load a markdown file using the text loader."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample.md"

    loader = FileIngestionLoader(str(fixture_path))
    documents = loader.load()

    assert len(documents) == 1
    assert "Sample Markdown Document" in documents[0].page_content
    assert documents[0].metadata["document_type"] == "markdown"
    assert documents[0].metadata["source"] == "sample.md"
    assert documents[0].metadata["encoding"] == "utf-8"


def test_pdf_loader(tmp_path):
    """Load a PDF using the PyMuPDF4LLM loader."""
    fitz = pytest.importorskip("fitz")
    pytest.importorskip("pymupdf4llm")

    pdf_path = tmp_path / "sample.pdf"
    pdf_document = fitz.open()
    page = pdf_document.new_page()
    page.insert_text((72, 72), "Hello PDF")
    pdf_document.save(pdf_path)
    pdf_document.close()

    loader = FileIngestionLoader(str(pdf_path))
    documents = loader.load()

    assert len(documents) == 1
    assert "hello pdf" in documents[0].page_content.lower()
    assert documents[0].metadata["document_type"] == "pdf"
    assert documents[0].metadata["page"] == 1
    assert documents[0].metadata["total_pages"] == 1
    assert documents[0].metadata["parser"] == "pymupdf4llm"


def test_loader_unsupported_file():
    """Raise error for unsupported extensions."""
    with pytest.raises(ValueError, match="Unsupported file type"):
        FileIngestionLoader("test.xyz")


def test_loader_file_not_found():
    """Raise error for missing files."""
    with pytest.raises(FileNotFoundError):
        FileIngestionLoader("nonexistent.txt")


def test_empty_file(tmp_path):
    """Raise error for empty content."""
    empty_path = tmp_path / "empty.txt"
    empty_path.write_text("", encoding="utf-8")

    loader = FileIngestionLoader(str(empty_path))
    with pytest.raises(ValueError, match="File is empty"):
        loader.load()
