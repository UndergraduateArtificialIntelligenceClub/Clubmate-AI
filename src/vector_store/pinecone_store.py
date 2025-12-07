"""Pinecone vector store integration."""

import logging
import time
from typing import List, Optional

from langchain.schema import Document
from langchain_pinecone import PineconeVectorStore
from pinecone import ServerlessSpec
from pinecone.grpc import PineconeGRPC as Pinecone

from src.embeddings.base import BaseEmbedder

logger = logging.getLogger(__name__)


class PineconeManager:
    """Manager for Pinecone vector database operations."""

    def __init__(
        self,
        api_key: str,
        environment: str,
        index_name: str,
        embedding_dimension: int
    ):
        """
        Initialize Pinecone manager.

        Args:
            api_key: Pinecone API key
            environment: Pinecone environment (e.g., 'us-west1-gcp')
            index_name: Name of the Pinecone index
            embedding_dimension: Dimension of embeddings
        """
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self.embedding_dimension = embedding_dimension

        # Initialize Pinecone client
        self.pc = Pinecone(api_key=api_key)

        logger.info(f"Initialized Pinecone client for environment: {environment}")

    def create_index_if_not_exists(self) -> None:
        """
        Create Pinecone index if it doesn't already exist.

        Uses serverless spec for cost-effective deployment.
        """
        existing_indexes = [index.name for index in self.pc.list_indexes()]

        if self.index_name in existing_indexes:
            logger.info(f"Index '{self.index_name}' already exists")
            return

        if self.index_name not in existing_indexes:
            logger.info(
                f"Creating new Pinecone index '{self.index_name}' "
                f"with dimension {self.embedding_dimension}"
            )

            self.pc.create_index(
                name=self.index_name,
                dimension=self.embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )

            # Wait for index to be ready
            logger.info("Waiting for index to be ready...")
            while not self.pc.describe_index(self.index_name).status.ready:
                time.sleep(1)

            logger.info(f"Index '{self.index_name}' created successfully")

    def get_index(self):
        """Get Pinecone index instance."""
        return self.pc.Index(self.index_name)

    def get_vector_store(self, embeddings: BaseEmbedder) -> PineconeVectorStore:
        """
        Get LangChain PineconeVectorStore interface.

        Args:
            embeddings: Embedding model to use

        Returns:
            PineconeVectorStore instance
        """
        # Ensure index exists
        self.create_index_if_not_exists()

        return PineconeVectorStore(
            index_name=self.index_name,
            embedding=embeddings,
            pinecone_api_key=self.api_key
        )

    def upsert_documents(
        self,
        documents: List[Document],
        embeddings: BaseEmbedder,
        batch_size: int = 100
    ) -> dict:
        """
        Upsert documents to Pinecone in batches.

        Args:
            documents: List of Document objects to upsert
            embeddings: Embedding model to use
            batch_size: Number of documents to upsert per batch

        Returns:
            Dictionary with upsert statistics
        """
        if not documents:
            logger.warning("No documents to upsert")
            return {"total": 0, "batches": 0}

        # Get vector store
        vector_store = self.get_vector_store(embeddings)

        # Upsert in batches
        total_docs = len(documents)
        num_batches = (total_docs + batch_size - 1) // batch_size

        logger.info(f"Upserting {total_docs} documents in {num_batches} batches")

        for i in range(0, total_docs, batch_size):
            batch = documents[i:i + batch_size]
            batch_num = (i // batch_size) + 1

            try:
                # Extract texts and metadatas
                texts = [doc.page_content for doc in batch]
                metadatas = [doc.metadata for doc in batch]

                # Add to vector store
                vector_store.add_texts(texts=texts, metadatas=metadatas)

                logger.info(f"Batch {batch_num}/{num_batches} upserted successfully")

            except Exception as e:
                logger.error(f"Failed to upsert batch {batch_num}: {e}")
                raise

        return {"total": total_docs, "batches": num_batches}

    def delete_all(self) -> None:
        """
        Delete all vectors from the index.

        WARNING: This operation cannot be undone!
        """
        logger.warning(f"Deleting all vectors from index '{self.index_name}'")

        index = self.get_index()

        try:
            # Delete all vectors
            index.delete(delete_all=True)
            logger.info("All vectors deleted successfully")
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            raise

    def get_stats(self) -> dict:
        """
        Get index statistics.

        Returns:
            Dictionary with index stats
        """
        index = self.get_index()
        stats = index.describe_index_stats()

        return {
            "total_vectors": stats.total_vector_count,
            "dimension": stats.dimension,
            "index_fullness": stats.index_fullness,
        }

    def index_exists(self) -> bool:
        """Check if index exists."""
        existing_indexes = [index.name for index in self.pc.list_indexes()]
        return self.index_name in existing_indexes
