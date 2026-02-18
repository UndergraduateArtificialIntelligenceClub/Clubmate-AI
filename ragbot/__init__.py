"""
Clubmate AI — RAG module public API.

Core functions:
    rag_ingest(path)           — Ingest a local file or directory
    rag_query(query)           — Query with LLM-generated answer
    rag_retrieve(query)        — Raw chunk retrieval (no LLM)
    rag_has_documents()        — Check if vector store has content
    db_reset()                 — Clear all documents

Source ingestion helpers:
    ingest_google_doc(url)     — Fetch a Google Doc and ingest
    ingest_uploaded_file(...)  — Ingest raw file bytes from API upload
"""

from .rag import rag_ingest, rag_query, db_reset, rag_retrieve, rag_has_documents, rag_chunk_count
from .sources.google_docs import ingest_google_doc
from .sources.file_upload import ingest_uploaded_file

__all__ = [
    "rag_ingest",
    "rag_query",
    "db_reset",
    "rag_retrieve",
    "rag_has_documents",
    "rag_chunk_count",
    "ingest_google_doc",
    "ingest_uploaded_file",
]
