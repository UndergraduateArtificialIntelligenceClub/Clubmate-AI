"""Unified file ingestion loader built on LangChain loaders."""

from pathlib import Path
from typing import Dict, Iterable, List

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document

try:
    from langchain_pymupdf4llm import PyMuPDF4LLMLoader
except ImportError:  # pragma: no cover - dependency handled at runtime
    PyMuPDF4LLMLoader = None  # type: ignore[misc,assignment]


class FileIngestionLoader:
    """Load supported files into LangChain Documents with normalized metadata."""

    _EXTENSION_MAP: Dict[str, str] = {
        ".txt": "text",
        ".md": "markdown",
        ".markdown": "markdown",
        ".pdf": "pdf",
    }
    _TEXT_EXTENSIONS = {".txt", ".md", ".markdown"}

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not self.file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        self.extension = self.file_path.suffix.lower()
        if self.extension not in self._EXTENSION_MAP:
            supported = ", ".join(sorted(self._EXTENSION_MAP.keys()))
            raise ValueError(
                f"Unsupported file type: {self.extension}. Supported types: {supported}"
            )

    @classmethod
    def supported_extensions(cls) -> Iterable[str]:
        """Return supported file extensions."""
        return cls._EXTENSION_MAP.keys()

    def load(self) -> List[Document]:
        """Load the file using the appropriate LangChain loader and normalize metadata."""
        documents = self._load_with_langchain()

        if not documents or all(not doc.page_content.strip() for doc in documents):
            raise ValueError(f"File is empty: {self.file_path}")

        return self._apply_metadata(documents)

    def _load_with_langchain(self) -> List[Document]:
        """Delegate file loading to the appropriate LangChain loader."""
        if self.extension in self._TEXT_EXTENSIONS:
            loader = TextLoader(str(self.file_path), encoding="utf-8")
        elif self.extension == ".pdf":
            if PyMuPDF4LLMLoader is None:
                raise ImportError(
                    "PyMuPDF4LLMLoader is not available. "
                    "Install the pymupdf4llm extra listed in pyproject.toml."
                )
            loader = PyMuPDF4LLMLoader(str(self.file_path))
        else:
            # This should not be reachable due to validation in __init__
            raise ValueError(f"No loader configured for extension: {self.extension}")

        return loader.load()

    def _apply_metadata(self, documents: List[Document]) -> List[Document]:
        """Attach standardized metadata to each document."""
        base_metadata = self._get_base_metadata()
        document_type = self._EXTENSION_MAP[self.extension]
        total_pages = len(documents) if self.extension == ".pdf" else None

        normalized_documents: List[Document] = []
        for index, document in enumerate(documents):
            metadata = {**document.metadata, **base_metadata}
            metadata["document_type"] = document_type

            if self.extension == ".pdf":
                metadata["page"] = index + 1
                metadata["total_pages"] = total_pages
                metadata["parser"] = "pymupdf4llm"
            elif self.extension in self._TEXT_EXTENSIONS:
                metadata["encoding"] = "utf-8"

            normalized_documents.append(
                Document(page_content=document.page_content, metadata=metadata)
            )

        return normalized_documents

    def _get_base_metadata(self) -> Dict[str, object]:
        """Compute metadata common to all documents."""
        stat = self.file_path.stat()
        return {
            "source": self.file_path.name,
            "file_path": str(self.file_path.resolve()),
            "file_size": stat.st_size,
            "modified_time": stat.st_mtime,
        }
