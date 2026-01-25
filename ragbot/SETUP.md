# RAG API - Quick Setup Guide

## 1. Setup Environment

Copy the example environment file and add your Google API key:

```bash
cd rag_api
cp .env.example .env
```

Edit `.env` and add your actual Google API key:
```bash
GOOGLE_API_KEY=your-actual-google-api-key-here
```

## 2. Test the API

Run the test script to verify everything works:

```bash
python test_api.py
```

You should see:
```
✓ GOOGLE_API_KEY is set
✓ Successfully imported rag_ingest and rag_query
✓ Ingestion successful
✓ Query successful
✅ All tests passed!
```

## 3. Try the Examples

```bash
python example.py
```

## 4. Use in Your Code

```python
from rag_api import rag_ingest, rag_query

# Ingest documents
success = rag_ingest("path/to/documents/")

# Query
answer = rag_query("What is this about?")
print(answer)
```

That's it! The RAG API is now ready to use.

## Configuration Options

Edit `rag_api/.env` to customize:

```bash
# Required
GOOGLE_API_KEY=your-key

# Optional (with defaults)
CHROMA_DB_DIR=./chroma_db                    # Vector storage location
CHROMA_COLLECTION_NAME=rag-documents         # Collection name
SENTENCE_TRANSFORMER_MODEL=BAAI/bge-base-en-v1.5  # Embedding model
DEFAULT_LLM_MODEL=gemini-2.0-flash-exp       # Default LLM
```

## Troubleshooting

**"GOOGLE_API_KEY not set"**
- Make sure you copied `.env.example` to `.env`
- Make sure you added your actual API key (not the placeholder)

**"No module named 'rag_api'"**
- Make sure you're running from the Clubmate-AI directory
- Or add the path: `sys.path.append('/path/to/Clubmate-AI')`

See [README.md](README.md) for full documentation.
