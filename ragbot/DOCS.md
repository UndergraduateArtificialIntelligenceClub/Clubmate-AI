# RAG API Module

A simple, self-contained API for document ingestion and querying using RAG (Retrieval-Augmented Generation).

## Features

- ✅ **Simple API**: Just two functions - `rag_ingest()` and `rag_query()`
- ✅ **Self-contained**: No dependency on `src/` directory
- ✅ **ChromaDB**: Local vector storage with automatic persistence
- ✅ **Semantic Chunking**: Intelligent document splitting
- ✅ **Google Gemini**: Powerful LLM for answer generation
- ✅ **Multiple Formats**: Supports PDF, Markdown, and text files

## Installation

This module is part of the Clubmate-AI project. Make sure all dependencies are installed:

```bash
cd /path/to/Clubmate-AI
uv sync  # or: pip install -e .
```

## Quick Start

### 1. Set Environment Variables

Create a `.env` file in the project root (or export variables):

```bash
# Required
GOOGLE_API_KEY=your-google-api-key-here

# Optional (defaults shown)
CHROMA_DB_DIR=./chroma_db
CHROMA_COLLECTION_NAME=rag-documents
SENTENCE_TRANSFORMER_MODEL=BAAI/bge-base-en-v1.5
```

### 2. Import and Use

```python
from rag_api import rag_ingest, rag_query

# Ingest documents (file or directory)
success = rag_ingest("path/to/documents/")
print(f"Ingestion successful: {success}")

# Query the system
answer = rag_query("What is this document about?")
print(answer)
```

## API Reference

### `rag_ingest(docpath: str) -> bool`

Ingest documents into the RAG system.

**Parameters:**
- `docpath` (str): Path to a file or directory
  - If directory: Recursively ingests all supported files
  - If file: Ingests the single file

**Returns:**
- `bool`: True if successful, False otherwise

**Supported Formats:**
- `.txt` - Plain text
- `.md`, `.markdown` - Markdown files
- `.pdf` - PDF documents

**Example:**
```python
# Ingest a single file
success = rag_ingest("report.pdf")

# Ingest a directory
success = rag_ingest("documents/")
```

---

### `rag_query(query: str, topk_results: Optional[int] = None, llm: Optional[str] = None) -> str`

Query the RAG system and get an AI-generated answer.

**Parameters:**
- `query` (str): Question to ask
- `topk_results` (Optional[int]): Number of document chunks to retrieve (default: 5)
- `llm` (Optional[str]): LLM model to use (default: "gemini-2.0-flash-exp")

**Returns:**
- `str`: Generated answer with citations

**Available LLM Models:**
- `gemini-2.0-flash-exp` (default) - Fast, efficient
- `gemini-2.5-flash-lite` - Lightweight
- `gemini-1.5-pro` - More powerful but slower
- Any other Google Gemini model

**Example:**
```python
# Basic query
answer = rag_query("What are the main findings?")

# Custom parameters
answer = rag_query(
    "Explain the methodology",
    topk_results=10,
    llm="gemini-2.5-flash-lite"
)
```

## Complete Example

```python
import os
from rag_api import rag_ingest, rag_query

# Set API key (or use .env file)
os.environ['GOOGLE_API_KEY'] = 'your-api-key'

# 1. Ingest documents
print("Ingesting documents...")
if rag_ingest("data/documents/"):
    print("✓ Ingestion successful")
else:
    print("✗ Ingestion failed")

# 2. Ask questions
questions = [
    "What is the main topic of these documents?",
    "What are the key findings?",
    "What recommendations are made?"
]

for question in questions:
    print(f"\nQ: {question}")
    answer = rag_query(question)
    print(f"A: {answer}\n")
    print("-" * 80)
```

## Integration in Other Projects

You can import this module from external Python projects:

```python
import sys
sys.path.append('/path/to/Clubmate-AI')

from rag_api import rag_ingest, rag_query

# Use as normal
rag_ingest("my_documents/")
answer = rag_query("My question?")
```

Or install the Clubmate-AI package:

```bash
pip install -e /path/to/Clubmate-AI
```

Then import normally:

```python
from rag_api import rag_ingest, rag_query
```

## How It Works

1. **Document Loading**: Loads files using LangChain loaders
2. **Semantic Chunking**: Splits documents at semantic boundaries
3. **Embedding**: Converts chunks to vectors using Sentence Transformers
4. **Storage**: Stores vectors in local ChromaDB database
5. **Retrieval**: Finds most relevant chunks for query
6. **Generation**: Uses Google Gemini to generate answer with citations

## Data Persistence

All ingested documents are stored locally in the `./chroma_db/` directory.

Data persists across Python sessions automatically. No need to re-ingest unless:
- You want to add new documents
- You change the embedding model
- You delete the ChromaDB directory

## Error Handling

```python
try:
    success = rag_ingest("nonexistent.pdf")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except ValueError as e:
    print(f"Invalid input: {e}")

try:
    answer = rag_query("")
except ValueError as e:
    print(f"Empty query: {e}")
```

## Troubleshooting

### "GOOGLE_API_KEY environment variable is required"
Set the Google API key in `.env` or export it:
```bash
export GOOGLE_API_KEY=your-key-here
```

### "PyMuPDF4LLMLoader not available"
Install the PDF parsing library:
```bash
pip install pymupdf4llm
```

### No results returned
- Ensure documents were successfully ingested
- Check that your query is related to ingested content
- Try increasing `topk_results`

## Configuration

All settings can be customized via environment variables:

```bash
# ChromaDB location
CHROMA_DB_DIR=./my_vector_db

# Collection name
CHROMA_COLLECTION_NAME=my-docs

# Embedding model
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2

# Google API key
GOOGLE_API_KEY=your-key
```

## License

MIT License (same as parent project)
