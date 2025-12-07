"""Document ingestion pipeline."""

import logging
from pathlib import Path
from typing import Dict, List

from src.document_loaders.file_ingestion import FileIngestionLoader
from src.chunking.semantic_chunker import DocumentChunker
from src.vector_store.pinecone_store import PineconeManager
from src.embeddings.base import BaseEmbedder

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Pipeline for ingesting documents into the vector store."""

    def __init__(
        self,
        chunker: DocumentChunker,
        vector_store_manager: PineconeManager,
        embeddings: BaseEmbedder
    ):
        """
        Initialize ingestion pipeline.

        Args:
            chunker: Document chunker instance
            vector_store_manager: Pinecone manager instance
            embeddings: Embedding model to use
        """
        self.chunker = chunker
        self.vector_store_manager = vector_store_manager
        self.embeddings = embeddings

    def ingest_file(self, file_path: str) -> Dict:
        """
        Ingest a single file through the complete pipeline.

        Workflow:
        1. Load document using appropriate loader
        2. Chunk document using semantic chunker
        3. Generate embeddings for chunks
        4. Upsert chunks to Pinecone

        Args:
            file_path: Path to file to ingest

        Returns:
            Dictionary with ingestion statistics
        """
        file_path_obj = Path(file_path)

        logger.info(f"Starting ingestion for file: {file_path}")

        try:
            # Step 1: Load document
            loader = FileIngestionLoader(file_path)
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} document(s) from {file_path_obj.name}")

            # Step 2: Chunk documents
            chunks = self.chunker.chunk_documents(documents)
            logger.info(f"Created {len(chunks)} chunks from {len(documents)} document(s)")

            if not chunks:
                logger.warning(f"No chunks created from {file_path_obj.name}")
                return {
                    "file": str(file_path_obj.name),
                    "status": "skipped",
                    "documents_loaded": len(documents),
                    "chunks_created": 0,
                    "chunks_upserted": 0,
                }

            # Step 3 & 4: Generate embeddings and upsert to Pinecone
            result = self.vector_store_manager.upsert_documents(
                documents=chunks,
                embeddings=self.embeddings
            )

            logger.info(
                f"Successfully ingested {file_path_obj.name}: "
                f"{result['total']} chunks in {result['batches']} batches"
            )

            return {
                "file": str(file_path_obj.name),
                "status": "success",
                "documents_loaded": len(documents),
                "chunks_created": len(chunks),
                "chunks_upserted": result['total'],
                "batches": result['batches'],
            }

        except Exception as e:
            logger.error(f"Failed to ingest {file_path_obj.name}: {e}")
            return {
                "file": str(file_path_obj.name),
                "status": "failed",
                "error": str(e),
            }

    def ingest_directory(
        self,
        directory_path: str,
        recursive: bool = False,
        skip_errors: bool = True
    ) -> Dict:
        """
        Ingest all supported files in a directory.

        Args:
            directory_path: Path to directory
            recursive: Whether to recursively search subdirectories
            skip_errors: Whether to continue if a file fails

        Returns:
            Dictionary with overall ingestion statistics
        """
        dir_path = Path(directory_path)

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")

        logger.info(f"Starting directory ingestion: {directory_path}")

        # Find all supported files
        supported_extensions = set(FileIngestionLoader.supported_extensions())
        pattern = "**/*" if recursive else "*"

        files = [
            f for f in dir_path.glob(pattern)
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]

        if not files:
            logger.warning(f"No supported files found in {directory_path}")
            return {
                "directory": str(dir_path),
                "total_files": 0,
                "successful": 0,
                "failed": 0,
                "skipped": 0,
                "results": [],
            }

        logger.info(f"Found {len(files)} file(s) to ingest")

        results = []
        successful = 0
        failed = 0
        skipped = 0

        for file_path in files:
            result = self.ingest_file(str(file_path))
            results.append(result)

            if result["status"] == "success":
                successful += 1
            elif result["status"] == "failed":
                failed += 1
                if not skip_errors:
                    raise Exception(f"Failed to ingest {file_path}: {result.get('error')}")
            elif result["status"] == "skipped":
                skipped += 1

        summary = {
            "directory": str(dir_path),
            "total_files": len(files),
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "results": results,
        }

        logger.info(
            f"Directory ingestion complete: "
            f"{successful} successful, {failed} failed, {skipped} skipped"
        )

        return summary
