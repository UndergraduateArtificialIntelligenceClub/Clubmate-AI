# Repository Guidelines

## Project Structure & Modules
- `main.py` is the Typer CLI entry point for `ingest`, `query`, `status`, and `reset`.
- `config/settings.py` holds Pydantic settings loaded from `.env`; update here when adding config.
- `src/document_loaders`, `src/chunking`, `src/embeddings`, `src/vector_store`, `src/retrieval`, `src/generation`, and `src/pipeline` contain the RAG components.
- `src/document_loaders/file_ingestion.py` is the single entry point for loading files (TextLoader for .txt/.md, PyMuPDF4LLMLoader for .pdf) with normalized metadata.
- `data/` stores local documents; keep large/raw files out of Git.
- Tests live in `tests/` with fixtures under `tests/fixtures/`; integration tests are marked with `@pytest.mark.integration`.

## Environment, Build, and Run
- Use Python 3.12+; the project expects the `uv`-managed virtualenv (`source .venv/bin/activate`).
- Install or refresh deps: `uv pip install -e .` (reads `pyproject.toml`/`uv.lock`).
- Check configuration and service access: `python main.py status`.
- Ingest content: `python main.py ingest data/documents/ --recursive`.
- Query the system: `python main.py query "Your question" --top-k 10 --no-sources`.
- Reset vector data (destructive): `python main.py reset`.

## Coding Style & Naming
- Follow PEP 8 with 4-space indentation; keep functions short and typed (`-> None` etc.).
- Use snake_case for modules, functions, and variables; PascalCase for classes.
- Prefer `pathlib.Path`, rich console output, and Typer options/help for CLI changes.
- Add docstrings to public functions/classes; keep messages concise and user-facing.

## Testing Guidelines
- Default: `pytest tests -m "not integration"` for fast feedback without external APIs.
- Full run (requires Pinecone/Gemini keys configured): `pytest`.
- Name tests `test_*.py` and functions `test_*`; cover new logic with unit tests and mark external calls as `integration`.
- If you add a new loader/chunker, include fixtures under `tests/fixtures/` and assert metadata is preserved.

## Commit & Pull Requests
- No existing history; use concise, imperative summaries (e.g., `Add markdown loader metadata`) and mention scope if helpful.
- In PRs, include: purpose, key changes, test command/results, and any config/env expectations. Link issues when applicable.
- Screenshots/log snippets are encouraged for UX or CLI output changes; omit secrets and `.env`.

## Security & Configuration
- Never commit `.env` or API keys; use `.env.example` as the template.
- Ensure Pinecone index names and embedding dimensions stay aligned with `config/settings.py::get_embedding_dimension`.
- Large document sets stay in `data/` locally; scrub sensitive content before sharing test fixtures.
