"""Semantic chunking using LangChain's SemanticChunker."""

from typing import List
import logging

from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker

from src.embeddings.base import BaseEmbedder

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Document chunker using semantic-based splitting."""

    def __init__(
        self,
        embeddings: BaseEmbedder,
        breakpoint_threshold_type: str = "percentile",
        breakpoint_threshold_amount: float = 95.0
    ):
        """
        Initialize semantic chunker.

        Args:
            embeddings: Embedding model to use for semantic similarity
            breakpoint_threshold_type: Type of threshold ("percentile", "standard_deviation", or "interquartile")
            breakpoint_threshold_amount: Amount for the threshold (e.g., 95 for 95th percentile)
        """
        self.embeddings = embeddings

        logger.info(
            f"Initializing SemanticChunker with {breakpoint_threshold_type} "
            f"threshold at {breakpoint_threshold_amount}"
        )

        # Create LangChain's SemanticChunker
        self.chunker = SemanticChunker(
            embeddings=embeddings,
            breakpoint_threshold_type=breakpoint_threshold_type,
            breakpoint_threshold_amount=breakpoint_threshold_amount
        )

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into semantic chunks.

        Args:
            documents: List of Document objects to chunk

        Returns:
            List of chunked Documents with preserved metadata plus chunk information
        """
        if not documents:
            return []

        all_chunks = []

        for doc in documents:
            # Skip empty documents
            if not doc.page_content.strip():
                logger.warning(f"Skipping empty document: {doc.metadata.get('source', 'unknown')}")
                continue

            try:
                # Use SemanticChunker to split the document
                chunks = self.chunker.split_documents([doc])

                # Add chunk metadata
                for idx, chunk in enumerate(chunks):
                    # Preserve original metadata
                    chunk.metadata.update(doc.metadata)

                    # Add chunk-specific metadata
                    chunk.metadata.update({
                        "chunk_index": idx,
                        "total_chunks": len(chunks),
                        "chunk_method": "semantic",
                    })

                all_chunks.extend(chunks)

                logger.debug(
                    f"Document '{doc.metadata.get('source', 'unknown')}' "
                    f"split into {len(chunks)} semantic chunks"
                )

            except Exception as e:
                logger.error(
                    f"Failed to chunk document '{doc.metadata.get('source', 'unknown')}': {e}"
                )
                # Continue with other documents
                continue

        logger.info(f"Total chunks created: {len(all_chunks)} from {len(documents)} documents")

        return all_chunks

    def chunk_text(self, text: str, metadata: dict = None) -> List[Document]:
        """
        Chunk a single text string into semantic chunks.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to chunks

        Returns:
            List of Document chunks
        """
        if not text.strip():
            return []

        # Create a temporary document
        doc = Document(page_content=text, metadata=metadata or {})

        return self.chunk_documents([doc])
