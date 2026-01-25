"""
RAG API - Core functionality for document ingestion and querying.

This module provides standalone RAG functionality without depending on the src/ directory.
"""

import logging
from pathlib import Path
from typing import Optional, List

# LangChain imports
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document as LCDocument
from langchain_experimental.text_splitter import SemanticChunker
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer

# ChromaDB (through LangChain)
# Note: Chroma handles client creation internally

# Local config
from .config import RAGConfig

# PDF loading
try:
    from langchain_pymupdf4llm import PyMuPDF4LLMLoader
except ImportError:
    PyMuPDF4LLMLoader = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SentenceTransformerEmbedder(Embeddings):
    """Sentence Transformer embeddings for LangChain."""
    
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        embedding = self.model.encode([text], convert_to_numpy=True)[0]
        return embedding.tolist()
    
    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._dimension


class RAGSystem:
    """Self-contained RAG system for ingestion and querying."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern to avoid reloading models."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize RAG system components (only once)."""
        if self._initialized:
            return
        
        logger.info("Initializing RAG system...")
        RAGConfig.validate()
        
        # Initialize embeddings
        logger.info(f"Loading embedding model: {RAGConfig.EMBEDDING_MODEL}")
        self.embeddings = SentenceTransformerEmbedder(RAGConfig.EMBEDDING_MODEL)
        
        # Initialize vector store (Chroma handles client creation internally)
        self.vector_store = Chroma(
            collection_name=RAGConfig.CHROMA_COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=RAGConfig.CHROMA_DB_DIR
        )
        
        # Initialize semantic chunker
        self.chunker = SemanticChunker(
            embeddings=self.embeddings,
            breakpoint_threshold_type=RAGConfig.CHUNK_THRESHOLD_TYPE,
            breakpoint_threshold_amount=RAGConfig.CHUNK_THRESHOLD_AMOUNT
        )
        
        logger.info("RAG system initialized successfully")
        self._initialized = True
    
    def load_document(self, file_path: str) -> List[LCDocument]:
        """Load a single document file."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        extension = path.suffix.lower()
        
        # Load based on file type
        if extension in ['.txt', '.md', '.markdown']:
            loader = TextLoader(str(path), encoding='utf-8')
        elif extension == '.pdf':
            if PyMuPDF4LLMLoader is None:
                raise ImportError("PyMuPDF4LLMLoader not available. Install pymupdf4llm.")
            loader = PyMuPDF4LLMLoader(str(path))
        else:
            raise ValueError(
                f"Unsupported file type: {extension}. "
                f"Supported: .txt, .md, .markdown, .pdf"
            )
        
        documents = loader.load()
        
        # Add metadata
        for doc in documents:
            doc.metadata['source'] = path.name
            doc.metadata['file_path'] = str(path.absolute())
        
        return documents
    
    def ingest_file(self, file_path: str) -> bool:
        """Ingest a single file into the vector store."""
        try:
            logger.info(f"Ingesting file: {file_path}")
            
            # Load document
            documents = self.load_document(file_path)
            logger.info(f"Loaded {len(documents)} document(s)")
            
            # Chunk documents
            chunks = self.chunker.split_documents(documents)
            logger.info(f"Created {len(chunks)} semantic chunks")
            
            if not chunks:
                logger.warning("No chunks created, skipping")
                return False
            
            # Add to vector store
            texts = [chunk.page_content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]
            self.vector_store.add_texts(texts=texts, metadatas=metadatas)
            
            logger.info(f"Successfully ingested {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to ingest {file_path}: {e}")
            return False
    
    def ingest_directory(self, dir_path: str, recursive: bool = True) -> bool:
        """Ingest all supported files in a directory."""
        path = Path(dir_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {dir_path}")
        
        # Find all supported files
        supported_extensions = {'.txt', '.md', '.markdown', '.pdf'}
        pattern = '**/*' if recursive else '*'
        
        files = [
            f for f in path.glob(pattern)
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]
        
        if not files:
            logger.warning(f"No supported files found in {dir_path}")
            return False
        
        logger.info(f"Found {len(files)} file(s) to ingest")
        
        # Ingest each file
        success_count = 0
        for file in files:
            if self.ingest_file(str(file)):
                success_count += 1
        
        logger.info(f"Successfully ingested {success_count}/{len(files)} files")
        return success_count > 0
    
    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        llm_model: Optional[str] = None,
        temperature: float = 0.7
    ) -> dict:
        """
        Query the RAG system.
        
        Args:
            question: Question to ask
            top_k: Number of chunks to retrieve (default: from config)
            llm_model: LLM model to use (default: gemini-2.0-flash-exp)
            temperature: LLM temperature (default: 0.7)
        
        Returns:
            Dictionary with:
                - generation (str): Generated answer
                - sources (list): List of source documents with metadata
        """
        if not question.strip():
            raise ValueError("Question cannot be empty")
        
        k = top_k if top_k is not None else RAGConfig.TOP_K_RESULTS
        model = llm_model if llm_model is not None else RAGConfig.DEFAULT_LLM_MODEL
        
        logger.info(f"Processing query: {question[:50]}...")
        
        # Retrieve relevant chunks
        results = self.vector_store.similarity_search_with_score(
            query=question,
            k=k
        )
        
        if not results:
            return {
                "generation": "I couldn't find any relevant information to answer your question.",
                "sources": []
            }
        
        logger.info(f"Retrieved {len(results)} chunks")
        
        # Format context and extract sources
        context_parts = []
        sources_dict = {}
        
        for idx, (doc, score) in enumerate(results, start=1):
            source = doc.metadata.get('source', 'unknown')
            page = doc.metadata.get('page')
            
            if page:
                citation = f"[{source}, page {page}]"
            else:
                citation = f"[{source}]"
            
            context_parts.append(f"Source {idx} {citation}:\n{doc.page_content}")
            
            # Track sources for output
            if source not in sources_dict:
                sources_dict[source] = {
                    "source": source,
                    "pages": set(),
                    "relevance_score": score
                }
            
            if page:
                sources_dict[source]["pages"].add(page)
            
            # Keep highest relevance score
            if score > sources_dict[source]["relevance_score"]:
                sources_dict[source]["relevance_score"] = score
        
        context = "\n---\n".join(context_parts)
        
        # TODO: Customize this further for FAQ-style responses, maybe local + fine tune...?
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
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Initialize LLM
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=RAGConfig.GOOGLE_API_KEY,
            temperature=temperature
        )
        
        # Generate answer
        formatted_prompt = prompt.format(context=context, question=question)
        response = llm.invoke(formatted_prompt)
        answer = response.content
        
        logger.info("Answer generated successfully")
        
        # Format sources for output
        sources = []
        for source_info in sources_dict.values():
            source_dict = {
                "source": source_info["source"],
                "relevance_score": float(source_info["relevance_score"])
            }
            
            if source_info["pages"]:
                source_dict["pages"] = sorted(list(source_info["pages"]))
            
            sources.append(source_dict)
        
        # Sort by relevance score (descending)
        sources.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return {
            "generation": answer,
            "sources": sources
        }
    
    def reset(self) -> bool:
        """
        Clear all documents from the vector database.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Resetting vector database...")
            
            # Delete the ChromaDB directory
            import shutil
            chroma_path = Path(RAGConfig.CHROMA_DB_DIR)
            
            if chroma_path.exists():
                shutil.rmtree(chroma_path)
                logger.info(f"Deleted ChromaDB directory: {chroma_path}")
                
                # Recreate the directory
                chroma_path.mkdir(parents=True, exist_ok=True)
                
                # Reinitialize vector store
                self.vector_store = Chroma(
                    collection_name=RAGConfig.CHROMA_COLLECTION_NAME,
                    embedding_function=self.embeddings,
                    persist_directory=RAGConfig.CHROMA_DB_DIR
                )
                
                logger.info("Vector database reset successfully")
                return True
            else:
                logger.warning("ChromaDB directory does not exist")
                return True  # Nothing to delete = success
                
        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            return False


# Global RAG instance
_rag = None


def _get_rag() -> RAGSystem:
    """Get or create RAG system instance."""
    global _rag
    if _rag is None:
        _rag = RAGSystem()
    return _rag


def rag_ingest(docpath: str) -> bool:
    """
    Ingest documents into the RAG system.
    
    Args:
        docpath: Path to a file or directory to ingest
    
    Returns:
        True if successful, False otherwise
    
    Example:
        >>> from rag_api import rag_ingest
        >>> success = rag_ingest("path/to/documents/")
        >>> print(f"Ingestion successful: {success}")
    """
    rag = _get_rag()
    
    path = Path(docpath)
    
    if path.is_file():
        return rag.ingest_file(docpath)
    elif path.is_dir():
        return rag.ingest_directory(docpath)
    else:
        raise ValueError(f"Path does not exist: {docpath}")


def rag_query(
    query: str,
    topk_results: Optional[int] = None,
    llm: Optional[str] = None
) -> dict:
    """
    Query the RAG system.
    
    Args:
        query: Question to ask
        topk_results: Number of chunks to retrieve (default: 5)
        llm: LLM model to use (default: gemini-2.0-flash-exp)
    
    Returns:
        Dictionary with:
            - generation (str): Generated answer with citations
            - sources (list): List of source documents with metadata
                - source (str): Document filename
                - relevance_score (float): Similarity score
                - pages (list[int], optional): Page numbers if PDF
    
    Example:
        >>> from rag_api import rag_query
        >>> result = rag_query("What is this document about?")
        >>> print(result["generation"])
        >>> print(result["sources"])
        
        >>> # Custom parameters
        >>> result = rag_query(
        ...     "Explain the key points",
        ...     topk_results=10,
        ...     llm="gemini-2.5-flash-lite"
        ... )
        >>> answer = result["generation"]
        >>> sources = result["sources"]
    """
    rag = _get_rag()
    return rag.query(
        question=query,
        top_k=topk_results,
        llm_model=llm
    )


def db_reset() -> bool:
    """
    Clear all documents from the vector database.
    
    WARNING: This operation cannot be undone! All ingested documents will be deleted.
    
    Returns:
        True if successful, False otherwise
    
    Example:
        >>> from rag_api import db_reset
        >>> success = db_reset()
        >>> if success:
        ...     print("Database cleared successfully")
    """
    rag = _get_rag()
    return rag.reset()

