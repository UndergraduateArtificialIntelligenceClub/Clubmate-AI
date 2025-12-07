"""Gemini-powered answer generation with citations."""

import logging
from typing import List, Tuple, Dict

from langchain.schema import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)


class GeminiGenerator:
    """Answer generator using Google's Gemini API with source citations."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-pro",
        temperature: float = 0.7
    ):
        """
        Initialize Gemini generator.

        Args:
            api_key: Google API key
            model: Gemini model name
            temperature: Temperature for generation (0.0 = deterministic, 2.0 = creative)
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature

        # Initialize LangChain Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature
        )

        self.prompt_template = self._create_prompt_template()

        logger.info(f"Initialized Gemini generator with model: {model}")

    def _create_prompt_template(self) -> PromptTemplate:
        """Create RAG prompt template with citation instructions."""
        template = """You are a helpful AI assistant that answers questions based on the provided context.

IMPORTANT INSTRUCTIONS:
1. Answer the question using ONLY information from the context below
2. Include citations by referencing the source documents in square brackets [source_name, page X]
3. If the context doesn't contain enough information to answer the question, say so clearly
4. Be concise but comprehensive
5. Maintain factual accuracy - don't make up information

Context:
{context}

Question: {question}

Answer with citations:"""

        return PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )

    def generate(
        self,
        query: str,
        retrieved_docs: List[Tuple[Document, float]]
    ) -> Dict:
        """
        Generate answer with citations based on retrieved documents.

        Args:
            query: User's question
            retrieved_docs: List of (Document, score) tuples from retrieval

        Returns:
            Dictionary containing:
                - answer: Generated answer with citations
                - sources: List of source dictionaries
                - retrieved_chunks: Number of chunks used
                - context_used: Formatted context string
        """
        if not retrieved_docs:
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "sources": [],
                "retrieved_chunks": 0,
                "context_used": "",
            }

        logger.info(f"Generating answer for query: {query[:50]}...")

        # Format context from retrieved documents
        context = self._format_context(retrieved_docs)

        # Generate answer using Gemini
        try:
            prompt = self.prompt_template.format(context=context, question=query)
            response = self.llm.invoke(prompt)

            answer = response.content

            # Extract and deduplicate sources
            sources = self._extract_sources(retrieved_docs)

            logger.info("Answer generated successfully")
            logger.debug(f"Answer length: {len(answer)} characters")

            return {
                "answer": answer,
                "sources": sources,
                "retrieved_chunks": len(retrieved_docs),
                "context_used": context,
            }

        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            raise

    def _format_context(self, retrieved_docs: List[Tuple[Document, float]]) -> str:
        """
        Format retrieved documents into context string.

        Args:
            retrieved_docs: List of (Document, score) tuples

        Returns:
            Formatted context string with citations
        """
        context_parts = []

        for idx, (doc, score) in enumerate(retrieved_docs, start=1):
            # Extract metadata
            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page")

            # Format citation
            if page:
                citation = f"[{source}, page {page}]"
            else:
                citation = f"[{source}]"

            # Format context chunk
            context_part = f"Source {idx} {citation}:\n{doc.page_content}\n"
            context_parts.append(context_part)

        return "\n---\n".join(context_parts)

    def _extract_sources(self, retrieved_docs: List[Tuple[Document, float]]) -> List[Dict]:
        """
        Extract and deduplicate source information.

        Args:
            retrieved_docs: List of (Document, score) tuples

        Returns:
            List of unique source dictionaries
        """
        sources_dict = {}

        for doc, score in retrieved_docs:
            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page")

            # Use source as key for deduplication
            if source not in sources_dict:
                sources_dict[source] = {
                    "source": source,
                    "pages": set(),
                    "max_score": score,
                }

            # Track pages
            if page:
                sources_dict[source]["pages"].add(page)

            # Update max score
            if score > sources_dict[source]["max_score"]:
                sources_dict[source]["max_score"] = score

        # Convert to list format
        sources = []
        for source_info in sources_dict.values():
            source_dict = {
                "source": source_info["source"],
                "relevance_score": source_info["max_score"],
            }

            # Add pages if available
            if source_info["pages"]:
                source_dict["pages"] = sorted(list(source_info["pages"]))

            sources.append(source_dict)

        # Sort by relevance score
        sources.sort(key=lambda x: x["relevance_score"], reverse=True)

        return sources

    def generate_streaming(
        self,
        query: str,
        retrieved_docs: List[Tuple[Document, float]]
    ):
        """
        Generate answer with streaming (for future CLI enhancement).

        Args:
            query: User's question
            retrieved_docs: List of (Document, score) tuples

        Yields:
            Chunks of generated text
        """
        if not retrieved_docs:
            yield "I couldn't find any relevant information to answer your question."
            return

        context = self._format_context(retrieved_docs)
        prompt = self.prompt_template.format(context=context, question=query)

        try:
            for chunk in self.llm.stream(prompt):
                if hasattr(chunk, 'content'):
                    yield chunk.content

        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            yield f"\n\nError: {e}"
