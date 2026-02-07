"""
RAG API - Simple interface for document ingestion and querying.

This module provides a clean API for using the RAG system in other applications.

Example:
    from rag_api import rag_ingest, rag_query, db_reset
    
    # Ingest documents
    success = rag_ingest("path/to/documents")
    
    # Query
    result = rag_query("What is this about?")
    print(result["generation"])
    
    # Reset database (clear all documents)
    db_reset()
"""

from .rag import rag_ingest, rag_query, db_reset, rag_retrieve, rag_has_documents

__all__ = ["rag_ingest", "rag_query", "db_reset", "rag_retrieve", "rag_has_documents"]
__version__ = "1.0.0"
