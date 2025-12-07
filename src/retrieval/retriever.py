"""Semantic retrieval module."""

import logging
from typing import List, Tuple, Optional

from langchain.schema import Document
from langchain_pinecone import PineconeVectorStore

logger = logging.getLogger(__name__)


class SemanticRetriever:
    """Semantic search and retrieval from vector store."""

    def __init__(self, vector_store: PineconeVectorStore, top_k: int = 5):
        """
        Initialize semantic retriever.

        Args:
            vector_store: LangChain PineconeVectorStore instance
            top_k: Number of top results to retrieve
        """
        self.vector_store = vector_store
        self.top_k = top_k

        logger.info(f"Initialized SemanticRetriever with top_k={top_k}")

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[dict] = None
    ) -> List[Tuple[Document, float]]:
        """
        Retrieve top-k most similar documents for a query.

        Args:
            query: Query string to search for
            top_k: Number of results to return (overrides default if provided)
            filter_metadata: Optional metadata filter (e.g., {"source": "report.pdf"})

        Returns:
            List of (Document, similarity_score) tuples, sorted by relevance
        """
        if not query.strip():
            raise ValueError("Query cannot be empty")

        k = top_k if top_k is not None else self.top_k

        logger.info(f"Retrieving top-{k} results for query: {query[:50]}...")

        try:
            # Perform similarity search with scores
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter_metadata
            )

            logger.info(f"Retrieved {len(results)} results")

            # Log top result for debugging
            if results:
                top_doc, top_score = results[0]
                logger.debug(
                    f"Top result (score: {top_score:.4f}): "
                    f"{top_doc.metadata.get('source', 'unknown')}"
                )

            return results

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            raise

    def retrieve_with_mmr(
        self,
        query: str,
        top_k: Optional[int] = None,
        fetch_k: int = 20,
        lambda_mult: float = 0.5
    ) -> List[Document]:
        """
        Retrieve documents using Maximum Marginal Relevance (MMR).

        MMR balances relevance and diversity to avoid redundant results.

        Args:
            query: Query string
            top_k: Number of results to return
            fetch_k: Number of documents to fetch before MMR reranking
            lambda_mult: Balance between relevance (1.0) and diversity (0.0)

        Returns:
            List of Documents (without scores)
        """
        k = top_k if top_k is not None else self.top_k

        logger.info(f"Retrieving top-{k} results using MMR for query: {query[:50]}...")

        try:
            results = self.vector_store.max_marginal_relevance_search(
                query=query,
                k=k,
                fetch_k=fetch_k,
                lambda_mult=lambda_mult
            )

            logger.info(f"MMR retrieved {len(results)} diverse results")

            return results

        except Exception as e:
            logger.error(f"MMR retrieval failed: {e}")
            raise

    def retrieve_by_metadata(
        self,
        query: str,
        metadata_filters: dict,
        top_k: Optional[int] = None
    ) -> List[Tuple[Document, float]]:
        """
        Retrieve documents filtered by metadata.

        Args:
            query: Query string
            metadata_filters: Metadata filters (e.g., {"source": "report.pdf", "page": 1})
            top_k: Number of results to return

        Returns:
            List of (Document, similarity_score) tuples
        """
        return self.retrieve(query=query, top_k=top_k, filter_metadata=metadata_filters)

    def get_sources(self, results: List[Tuple[Document, float]]) -> List[dict]:
        """
        Extract unique source information from retrieval results.

        Args:
            results: List of (Document, score) tuples from retrieve()

        Returns:
            List of dictionaries with source information
        """
        sources = []
        seen_sources = set()

        for doc, score in results:
            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page")

            # Create unique identifier
            identifier = f"{source}:{page}" if page else source

            if identifier not in seen_sources:
                seen_sources.add(identifier)

                source_info = {
                    "source": source,
                    "score": score,
                }

                if page:
                    source_info["page"] = page

                if "chunk_index" in doc.metadata:
                    source_info["chunk"] = doc.metadata["chunk_index"]

                sources.append(source_info)

        return sources
