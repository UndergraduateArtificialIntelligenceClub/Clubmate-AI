# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a RAG (Retrieval-Augmented Generation) implementation designed to:
- Ingest and process PDF/markdown/text files
- Generate vector embeddings and store them in Pinecone
- Perform semantic search to retrieve relevant document chunks
- Generate contextual answers using Gemini API with source citations

The project uses LangChain for orchestration and is built with Python 3.12.

## Development Setup

**Package Manager**: This project uses `uv` (not pip) for all package management.

### Installing Dependencies
```bash
uv pip install <package-name>
```

### Running the Application
```bash
# Check system status
python main.py status

# Ingest documents
python main.py ingest data/documents/

# Query the system
python main.py query "Your question here"

# Reset database
python main.py reset
```

### Activating Virtual Environment
The virtual environment is located at `.venv/`. Activate with:
```bash
source .venv/bin/activate
```

### Running Tests
```bash
pytest tests/
```

## Key Technology Stack

- **Python Version**: 3.12 (specified in `.python-version`)
- **Package Manager**: uv
- **Orchestration**: LangChain
- **Vector Database**: Pinecone
- **LLM**: Gemini API
- **Document Types**: PDF, Markdown, Text files

## Architecture Notes

### RAG Pipeline Flow
1. **Document Ingestion**: Parse PDF/markdown/text files
2. **Chunking**: Split documents into manageable chunks
3. **Embedding**: Convert chunks to vector embeddings
4. **Storage**: Store embeddings in Pinecone vector database
5. **Query Processing**: Convert user query to embedding
6. **Retrieval**: Perform semantic search (top-k similarity) against Pinecone
7. **Generation**: Use Gemini API to generate answers from retrieved chunks with citations

## Module Architecture

### Core Components

**config/settings.py**
- Pydantic-based configuration management
- Loads settings from `.env` file
- Validates API keys and parameters
- Get settings: `from config.settings import get_settings`

**src/document_loaders/**
- `file_ingestion.py`: Single entry point using LangChain TextLoader (.txt/.md) and PyMuPDF4LLMLoader (.pdf) with normalized metadata

**src/embeddings/**
- `base.py`: BaseEmbedder interface and EmbedderFactory
- `sentence_transformer.py`: Local sentence-transformers (384 dimensions)
- `google_embedder.py`: Google embeddings API (768 dimensions)

**src/chunking/**
- `semantic_chunker.py`: LangChain SemanticChunker wrapper
- Preserves metadata through chunking
- Adds chunk_index and total_chunks to metadata

**src/vector_store/**
- `pinecone_store.py`: Pinecone integration
- Auto-creates index if not exists
- Validates dimension matches embeddings
- Batch upsert for efficiency

**src/retrieval/**
- `retriever.py`: Semantic search with Pinecone
- Supports standard similarity search and MMR
- Returns (Document, score) tuples

**src/generation/**
- `gemini_generator.py`: Answer generation with Gemini
- Includes prompt template for citations
- Formats context from retrieved chunks
- Deduplicates sources

**src/pipeline/**
- `ingestion.py`: Load → Chunk → Embed → Store
- `query.py`: Retrieve → Generate with citations

**main.py**
- CLI with Typer and Rich
- Commands: ingest, query, reset, status
- Environment validation on startup

### Important Considerations
- Always use `uv` for package installation, never `pip`
- Embedding dimension must match Pinecone index dimension
- Switching embedding models requires new index or re-ingestion
- SemanticChunker requires an embeddings model
- All API keys validated at startup
- User must fill in actual API keys in `.env` file
- Always update CLAUDE.md after making any changes.
