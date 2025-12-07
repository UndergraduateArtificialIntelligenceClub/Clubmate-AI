"""Query processing pipeline."""

import logging
from typing import Dict, Optional

from src.retrieval.retriever import SemanticRetriever
from src.generation.gemini_generator import GeminiGenerator

logger = logging.getLogger(__name__)


class QueryPipeline:
    """Pipeline for processing queries through retrieval and generation."""

    def __init__(
        self,
        retriever: SemanticRetriever,
        generator: GeminiGenerator
    ):
        """
        Initialize query pipeline.

        Args:
            retriever: Semantic retriever instance
            generator: Gemini generator instance
        """
        self.retriever = retriever
        self.generator = generator

        logger.info("Initialized QueryPipeline")

    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        use_mmr: bool = False
    ) -> Dict:
        """
        Process query end-to-end: retrieve → generate.

        Workflow:
        1. Retrieve top-k relevant chunks from vector store
        2. Generate answer with Gemini using retrieved context
        3. Extract and format citations

        Args:
            question: User's question
            top_k: Number of chunks to retrieve (uses retriever default if None)
            use_mmr: Whether to use MMR for diverse results

        Returns:
            Dictionary containing:
                - question: Original question
                - answer: Generated answer with citations
                - sources: List of source documents
                - retrieved_chunks: Number of chunks retrieved
                - retrieval_method: "semantic" or "mmr"
        """
        if not question.strip():
            raise ValueError("Question cannot be empty")

        logger.info(f"Processing query: {question[:50]}...")

        # Step 1: Retrieve relevant chunks
        if use_mmr:
            logger.info("Using MMR retrieval for diversity")
            retrieved_docs = self.retriever.retrieve_with_mmr(
                query=question,
                top_k=top_k
            )
            # Convert to (doc, score) tuples with dummy scores for MMR
            retrieved_docs_with_scores = [(doc, 0.0) for doc in retrieved_docs]
            retrieval_method = "mmr"
        else:
            logger.info("Using standard semantic retrieval")
            retrieved_docs_with_scores = self.retriever.retrieve(
                query=question,
                top_k=top_k
            )
            retrieval_method = "semantic"

        logger.info(f"Retrieved {len(retrieved_docs_with_scores)} chunks")

        # Step 2: Generate answer with citations
        generation_result = self.generator.generate(
            query=question,
            retrieved_docs=retrieved_docs_with_scores
        )

        # Step 3: Format final response
        response = {
            "question": question,
            "answer": generation_result["answer"],
            "sources": generation_result["sources"],
            "retrieved_chunks": generation_result["retrieved_chunks"],
            "retrieval_method": retrieval_method,
        }

        logger.info("Query processing complete")

        return response

    def query_with_filter(
        self,
        question: str,
        metadata_filter: dict,
        top_k: Optional[int] = None
    ) -> Dict:
        """
        Process query with metadata filtering.

        Args:
            question: User's question
            metadata_filter: Metadata filters (e.g., {"source": "report.pdf"})
            top_k: Number of chunks to retrieve

        Returns:
            Query result dictionary
        """
        logger.info(f"Processing filtered query with filters: {metadata_filter}")

        # Retrieve with metadata filter
        retrieved_docs_with_scores = self.retriever.retrieve_by_metadata(
            query=question,
            metadata_filters=metadata_filter,
            top_k=top_k
        )

        logger.info(f"Retrieved {len(retrieved_docs_with_scores)} filtered chunks")

        # Generate answer
        generation_result = self.generator.generate(
            query=question,
            retrieved_docs=retrieved_docs_with_scores
        )

        # Format response
        response = {
            "question": question,
            "answer": generation_result["answer"],
            "sources": generation_result["sources"],
            "retrieved_chunks": generation_result["retrieved_chunks"],
            "retrieval_method": "filtered_semantic",
            "filters_applied": metadata_filter,
        }

        return response
