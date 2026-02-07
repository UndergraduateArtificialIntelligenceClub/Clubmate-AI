# Clubmate-AI Progress Tracker

## Completed ✅

### Core Setup
- [x] Consolidation of RAG module and Discord bot
- [x] Installed libs in venv
- [x] Git remote configured: `UndergraduateArtificialIntelligenceClub/Clubmate-AI`

### RAG Module Optimizations (Feb 7, 2026)
- [x] **Condensed logging** — Clean single-line logs with `%(message)s` format
- [x] **Suppressed noisy libraries** — urllib3, filelock, chromadb, huggingface_hub, etc.
- [x] **HuggingFaceEmbeddings** — Replaced custom `SentenceTransformerEmbedder` with `langchain_huggingface`
- [x] **test_rag.py improvements**:
  - Dual logging modes (`-v` for verbose)
  - Combined `setup()` function
  - Lazy-loaded `get_ragbot()` cache
  - `embed-test` command for testing embeddings

### Discord Bot
- [x] Basic commands: `!chat`, `!servers`, `!connect`, `!tools`, `!clear`
- [x] RAG commands: `!ingest`, `!rag-reset`
- [x] MCP server integration (calendar, example)

---

## In Progress 🔄

- [ ] Testing and performance validation

---

## Known Issues 🐛

### 1. ChromaDB File Locking (Windows)
```
[WinError 32] The process cannot access the file because it is being used by another process
```
- **When**: Running `!rag-reset` or `python test_rag.py reset` while Discord bot is running
- **Workaround**: Stop the bot before resetting
- **TODO**: Implement `vector_store.delete()` instead of `shutil.rmtree()`

## TODO 📋

### High Priority
- [ ] **`!status` command** — Comprehensive status showing:
  - Bot latency
  - Connected MCP servers (🟢/🔴)
  - RAG system status (docs count, ChromaDB size)
  - Available tools count

- [ ] **`!ingest \dir` syntax** — Directory disambiguation:
  - `!ingest path` → Auto-detect
  - `!ingest \path` → Force directory

### Nice to Have
- [ ] GPU detection for embeddings (currently CPU-only)
- [ ] `/` slash commands migration
- [ ] `!summarize` command for URLs/channels
- [ ] `!remind` command integration with calendar

---

*Last updated: Feb 7, 2026, 04:04 AM*
