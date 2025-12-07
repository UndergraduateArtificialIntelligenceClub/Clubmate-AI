# RAG Implementation

A production-ready Retrieval-Augmented Generation (RAG) system using LangChain, Pinecone, and Google Gemini.

## Features
- **Semantic Chunking**: Intelligent document splitting using LangChain's SemanticChunker
- **Vector Storage**: Pinecone for scalable vector search
- **AI Generation**: Google Gemini for answer generation with source citations
- **Document Support**: PDF, Markdown, and plain text files
- **CLI Interface**: Beautiful command-line interface with Rich formatting

## Prerequisites

- Python 3.12+
- Pinecone API key ([Get one here](https://www.pinecone.io/))
- Google API key for Gemini ([Get one here](https://makersuite.google.com/app/apikey))

## Installation

1. **Clone the repository** (or navigate to your project directory):
   ```bash
   cd rag-implementation
   ```

2. **Activate virtual environment**:
   ```bash
   source .venv/bin/activate
   ```

3. **Dependencies are already installed via uv**

## Configuration

1. **Copy the environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your API keys**:
   ```env
   PINECONE_API_KEY=your-actual-pinecone-api-key
   GOOGLE_API_KEY=your-actual-google-api-key
   ```

3. **Configure other settings** (optional):
   - `EMBEDDING_MODEL`: Choose `sentence-transformers` (local, free)
   - `CHUNK_SIZE`, `CHUNK_OVERLAP`: Adjust chunking parameters
   - `TOP_K_RESULTS`: Number of results to retrieve

## Usage

### Check System Status

```bash
python main.py status
```

This validates your configuration and shows Pinecone index statistics.

### Ingest Documents

**Ingest a single file**:
```bash
python main.py ingest path/to/document.pdf
```

**Ingest a directory**:
```bash
python main.py ingest path/to/documents/
```

**Ingest recursively**:
```bash
python main.py ingest path/to/documents/ --recursive
```

Supported formats: `.pdf`, `.md`, `.markdown`, `.txt`

### Query the System

```bash
python main.py query "What are the main findings?"
```

**Advanced options**:
```bash
# Retrieve more context
python main.py query "Your question" --top-k 10

# Hide sources
python main.py query "Your question" --no-sources
```

### Reset Database

```bash
python main.py reset
```

Deletes all documents from the vector database (requires confirmation).

## Project Structure

```
rag-implementation/
├── config/
│   └── settings.py           # Configuration management
├── src/
│   ├── document_loaders/     # File ingestion using LangChain loaders
│   ├── chunking/             # Semantic chunking
│   ├── embeddings/           # Dual embedding support
│   ├── vector_store/         # Pinecone integration
│   ├── retrieval/            # Semantic search
│   ├── generation/           # Gemini answer generation
│   └── pipeline/             # Ingestion and query pipelines
├── main.py                   # CLI entry point
├── .env                      # Your API keys (not in git)
└── data/documents/           # Place your documents here
```

## Example Workflow

1. **Check status**:
   ```bash
   python main.py status
   ```

2. **Add documents to `data/documents/`**

3. **Ingest them**:
   ```bash
   python main.py ingest data/documents/ --recursive
   ```

4. **Ask questions**:
   ```bash
   python main.py query "What is the summary of the reports?"
   ```

## Configuration Options

### Embedding Models

**Sentence Transformers** (default, local, free):
```env
EMBEDDING_MODEL=sentence-transformers
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
```

**Google Embeddings** (API-based, higher quality):
```env
EMBEDDING_MODEL=google
GOOGLE_EMBEDDING_MODEL=models/embedding-001
```

**Note**: Switching embedding models requires creating a new Pinecone index or re-ingesting all documents due to different dimensions.

### RAG Parameters

- `CHUNK_SIZE`: Target size for document chunks (default: 1000)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 200)
- `TOP_K_RESULTS`: Number of chunks to retrieve (default: 5)
- `TEMPERATURE`: LLM creativity (0.0-2.0, default: 0.7)

## Troubleshooting

### "Pinecone API Key: Missing or invalid"

Edit `.env` and add your Pinecone API key.

### "Google API Key: Missing or invalid"

Edit `.env` and add your Google API key.

### "No text content found in PDF"

The PDF may be scanned images. Use OCR to extract text first.

### Dimension mismatch error

You switched embedding models but the Pinecone index was created with a different dimension. Either:
- Create a new index with a different name
- Reset the database: `python main.py reset`
- Change back to the original embedding model

### Out of memory

Reduce batch size or use a smaller embedding model (all-MiniLM-L6-v2 is lightweight).

## Development

### Document Loading

File ingestion is centralized in `src/document_loaders/file_ingestion.py`, which wraps LangChain loaders (`TextLoader` for `.txt/.md`, `PyMuPDF4LLMLoader` for `.pdf`) and normalizes metadata. To support a new format, extend `_EXTENSION_MAP`, add the corresponding LangChain loader, and update ingestion tests.

### Running Tests

```bash
pytest tests/
```

## License

This project is available under the MIT License.
