#!/usr/bin/env python3
"""
RAG Module Test Script
======================
A comprehensive test script for the RAG module with detailed logging.
Run this to test ingestion, retrieval, and query functionality independently.

Usage:
    python test_rag.py ingest <path>    # Ingest a file or directory
    python test_rag.py query <question> # Query the knowledge base
    python test_rag.py retrieve <query> # Raw retrieval without LLM
    python test_rag.py status           # Check RAG system status
    python test_rag.py reset            # Reset the database
    python test_rag.py embed-test       # Test langchain_huggingface embeddings

Options:
    -v, --verbose    Enable verbose logging (default: quiet mode)
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Check for verbose mode
VERBOSE = '-v' in sys.argv or '--verbose' in sys.argv
if VERBOSE:
    sys.argv = [arg for arg in sys.argv if arg not in ('-v', '--verbose')]

def setup_logging(verbose: bool = False):
    """Configure logging based on mode."""
    if verbose:
        # Verbose mode: detailed multi-line logs
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s',
            datefmt='%H:%M:%S'
        )
        # Suppress noisy low-value logs even in verbose mode
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)  # Suppress connection pool spam
        logging.getLogger('filelock').setLevel(logging.WARNING)  # Suppress lock acquire/release
        logging.getLogger('chromadb.telemetry').setLevel(logging.WARNING)  # Suppress telemetry notice
        logging.getLogger('chromadb.config').setLevel(logging.WARNING)  # Suppress component start logs
    else:
        # Quiet mode: minimal one-line logs
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s'
        )
        # Suppress all external library logs in quiet mode
        logging.getLogger('httpx').setLevel(logging.ERROR)
        logging.getLogger('httpcore').setLevel(logging.ERROR)
        logging.getLogger('chromadb').setLevel(logging.ERROR)
        logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        logging.getLogger('filelock').setLevel(logging.ERROR)
        logging.getLogger('langchain_community').setLevel(logging.ERROR)
        logging.getLogger('langchain_core').setLevel(logging.ERROR)
        logging.getLogger('huggingface_hub').setLevel(logging.ERROR)
        logging.getLogger('ragbot').setLevel(logging.WARNING)

setup_logging(VERBOSE)
logger = logging.getLogger('RAG_TEST')

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_section(title: str):
    """Print a section divider."""
    print(f"\n--- {title} ---")

# Lazy-loaded ragbot module cache
_ragbot_cache = {}

def get_ragbot():
    """Lazy-load ragbot modules (avoids repeated import overhead)."""
    if not _ragbot_cache:
        from ragbot import rag_ingest, rag_query, db_reset, rag_retrieve, rag_has_documents
        from ragbot.config import RAGConfig
        _ragbot_cache.update({
            'ingest': rag_ingest,
            'query': rag_query,
            'reset': db_reset,
            'retrieve': rag_retrieve,
            'has_docs': rag_has_documents,
            'config': RAGConfig
        })
    return _ragbot_cache

def setup():
    """Initialize and validate RAG system (combines import test + config validation)."""
    print_header("SETUP")
    
    # Test imports
    print_section("Imports")
    try:
        logger.info("Loading ragbot module...")
        ragbot = get_ragbot()
        logger.info("✅ ragbot loaded")
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False
    
    # Show configuration
    print_section("Configuration")
    RAGConfig = ragbot['config']
    status = RAGConfig.get_status()
    for key, value in status.items():
        if 'api_key' in key.lower() and value:
            value = "****" + str(value)[-4:] if len(str(value)) > 4 else "****"
        print(f"  {key}: {value}")
    
    # Validate
    try:
        RAGConfig.validate()
        logger.info("✅ Configuration valid")
        return True
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        return False

def test_status():
    """Check RAG system status."""
    print_header("RAG SYSTEM STATUS")
    
    ragbot = get_ragbot()
    has_docs = ragbot['has_docs']
    RAGConfig = ragbot['config']
    
    print_section("Document Status")
    print(f"  Documents ingested: {'Yes' if has_docs() else 'No'}")
    
    print_section("ChromaDB Location")
    print(f"  Path: {RAGConfig.CHROMA_DB_DIR}")
    
    chroma_path = Path(RAGConfig.CHROMA_DB_DIR)
    if chroma_path.exists():
        files = list(chroma_path.rglob('*'))
        print(f"  Files: {len([f for f in files if f.is_file()])}")
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        print(f"  Total size: {total_size / 1024:.2f} KB")
    else:
        print("  Status: Not created yet")
    
    return True

def test_ingest(path: str):
    """Test document ingestion with detailed logging."""
    print_header(f"INGESTING: {path}")
    
    rag_ingest = get_ragbot()['ingest']
    
    path_obj = Path(path)
    
    print_section("Input Validation")
    print(f"  Path: {path_obj.absolute()}")
    print(f"  Exists: {path_obj.exists()}")
    print(f"  Type: {'Directory' if path_obj.is_dir() else 'File'}")
    
    if not path_obj.exists():
        logger.error(f"❌ Path does not exist: {path}")
        return False
    
    if path_obj.is_file():
        print(f"  Extension: {path_obj.suffix}")
        print(f"  Size: {path_obj.stat().st_size / 1024:.2f} KB")
    else:
        supported = ['.txt', '.md', '.markdown', '.pdf']
        files = [f for f in path_obj.rglob('*') if f.suffix.lower() in supported]
        print(f"  Supported files found: {len(files)}")
        for f in files[:10]:  # Show first 10
            print(f"    - {f.name}")
        if len(files) > 10:
            print(f"    ... and {len(files) - 10} more")
    
    print_section("Ingestion Process")
    start_time = datetime.now()
    
    try:
        success = rag_ingest(path)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if success:
            logger.info(f"✅ Ingestion completed in {elapsed:.2f}s")
        else:
            logger.warning(f"⚠️ Ingestion completed but no documents were processed")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_retrieve(query: str, top_k: int = 5):
    """Test raw retrieval (no LLM) with detailed output."""
    print_header(f"RAW RETRIEVAL: {query[:50]}...")
    
    ragbot = get_ragbot()
    rag_retrieve = ragbot['retrieve']
    
    print_section("Pre-check")
    has_docs = ragbot['has_docs']()
    print(f"  Documents available: {has_docs}")
    
    if not has_docs:
        logger.warning("⚠️ No documents in the knowledge base. Ingest some first!")
        return []
    
    print_section("Retrieval Parameters")
    print(f"  Query: {query}")
    print(f"  Top K: {top_k}")
    
    print_section("Retrieval Process")
    start_time = datetime.now()
    
    try:
        chunks = rag_retrieve(query, top_k=top_k)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Retrieved {len(chunks)} chunks in {elapsed:.2f}s")
        
        print_section(f"Retrieved Chunks ({len(chunks)})")
        for i, chunk in enumerate(chunks, 1):
            print(f"\n  [{i}] Source: {chunk['source']}")
            print(f"      Score: {chunk['relevance_score']:.4f}")
            if chunk.get('page'):
                print(f"      Page: {chunk['page']}")
            print(f"      Content Preview:")
            content = chunk['content'][:300].replace('\n', ' ').strip()
            print(f"      {content}...")
        
        return chunks
        
    except Exception as e:
        logger.error(f"❌ Retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_query(question: str, top_k: int = 5):
    """Test full RAG query with LLM generation."""
    print_header(f"FULL RAG QUERY: {question[:50]}...")
    
    ragbot = get_ragbot()
    rag_query = ragbot['query']
    
    print_section("Pre-check")
    has_docs = ragbot['has_docs']()
    print(f"  Documents available: {has_docs}")
    
    if not has_docs:
        logger.warning("⚠️ No documents in the knowledge base. Ingest some first!")
        return None
    
    print_section("Query Parameters")
    print(f"  Question: {question}")
    print(f"  Top K: {top_k}")
    
    print_section("Query Process")
    start_time = datetime.now()
    
    try:
        result = rag_query(question, topk_results=top_k)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Query completed in {elapsed:.2f}s")
        
        print_section("Generated Answer")
        print(f"\n{result['generation']}\n")
        
        print_section("Sources Used")
        for source in result['sources']:
            print(f"  - {source['source']} (score: {source['relevance_score']:.4f})")
            if source.get('pages'):
                print(f"    Pages: {source['pages']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_reset():
    """Reset the RAG database."""
    print_header("RESETTING DATABASE")
    
    db_reset = get_ragbot()['reset']
    
    print_section("Confirmation")
    response = input("  Are you sure you want to delete all ingested documents? (yes/no): ")
    
    if response.lower() != 'yes':
        print("  Cancelled.")
        return False
    
    print_section("Reset Process")
    try:
        success = db_reset()
        if success:
            logger.info("✅ Database reset successfully")
        else:
            logger.error("❌ Reset failed")
        return success
    except Exception as e:
        logger.error(f"❌ Reset failed: {e}")
        return False

def test_embeddings():
    """Test langchain_huggingface embeddings with GPU/CPU detection."""
    print_header("TESTING LANGCHAIN_HUGGINGFACE EMBEDDINGS")
    
    # Hardware - defaulting to CPU for now
    # TODO: GPU detection needs work - see commented code below
    print_section("Hardware")
    device = 'cpu'
    print(f"  Device: {device.upper()}")
    
    # --- GPU DETECTION (commented out for now) ---
    # try:
    #     import torch
    #     if torch.cuda.is_available():
    #         device = 'cuda'
    #         gpu_name = torch.cuda.get_device_name(0)
    #         # Check for AMD ROCm vs NVIDIA CUDA
    #         if hasattr(torch.version, 'hip') and torch.version.hip is not None:
    #             logger.info(f"✅ AMD ROCm: {gpu_name}")
    #         else:
    #             logger.info(f"✅ NVIDIA CUDA: {gpu_name}")
    #     elif hasattr(torch, 'xpu') and torch.xpu.is_available():
    #         device = 'xpu'
    #         logger.info("✅ Intel XPU available")
    # except ImportError:
    #     pass
    # --- END GPU DETECTION ---
    
    # Test langchain_huggingface import
    print_section("Import Test")
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        logger.info("✅ langchain_huggingface imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import langchain_huggingface: {e}")
        print("\n  To install, run:")
        print("  pip install langchain-huggingface")
        return False
    
    # Initialize embeddings
    print_section("Initializing Embeddings")
    model_name = "BAAI/bge-large-en-v1.5"
    print(f"  Model: {model_name}")
    print(f"  Device: {device}")
    print(f"  Normalize: True")
    
    start_time = datetime.now()
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True}
        )
        load_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Model loaded in {load_time:.2f}s")
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test embedding generation
    print_section("Embedding Generation Test")
    test_texts = [
        "What is the capital of France?",
        "Paris is the capital and largest city of France.",
        "The quick brown fox jumps over the lazy dog.",
    ]
    
    print(f"  Test texts: {len(test_texts)}")
    for i, text in enumerate(test_texts, 1):
        print(f"    [{i}] {text[:50]}...")
    
    start_time = datetime.now()
    try:
        embeddings_result = embeddings.embed_documents(test_texts)
        embed_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Generated {len(embeddings_result)} embeddings in {embed_time:.3f}s")
        
        print_section("Embedding Details")
        print(f"  Number of embeddings: {len(embeddings_result)}")
        print(f"  Embedding dimension: {len(embeddings_result[0])}")
        print(f"  Time per embedding: {embed_time / len(test_texts) * 1000:.1f}ms")
        
        # Show first few values of first embedding
        print(f"  First embedding (first 5 values): {embeddings_result[0][:5]}")
        
    except Exception as e:
        logger.error(f"❌ Embedding generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test similarity (to validate embeddings are meaningful)
    print_section("Similarity Test")
    try:
        import numpy as np
        
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        # Text 0 and 1 should be more similar (both about France/Paris)
        # Text 2 is unrelated
        sim_0_1 = cosine_similarity(embeddings_result[0], embeddings_result[1])
        sim_0_2 = cosine_similarity(embeddings_result[0], embeddings_result[2])
        sim_1_2 = cosine_similarity(embeddings_result[1], embeddings_result[2])
        
        print(f"  Similarity (Q about France ↔ A about Paris): {sim_0_1:.4f}")
        print(f"  Similarity (Q about France ↔ Random text):  {sim_0_2:.4f}")
        print(f"  Similarity (A about Paris ↔ Random text):   {sim_1_2:.4f}")
        
        if sim_0_1 > sim_0_2 and sim_0_1 > sim_1_2:
            logger.info("✅ Semantic similarity is working correctly!")
        else:
            logger.warning("⚠️ Similarity scores are unexpected - model may need verification")
            
    except ImportError:
        logger.warning("⚠️ NumPy not available for similarity test")
    
    # Test query embedding
    print_section("Query Embedding Test")
    start_time = datetime.now()
    query_embedding = embeddings.embed_query("What is the population of Paris?")
    query_time = (datetime.now() - start_time).total_seconds()
    
    print(f"  Query: 'What is the population of Paris?'")
    print(f"  Dimension: {len(query_embedding)}")
    print(f"  Time: {query_time * 1000:.1f}ms")
    logger.info(f"✅ Query embedding generated in {query_time * 1000:.1f}ms")
    
    print_section("Summary")
    print(f"  ✅ Model: {model_name}")
    print(f"  ✅ Device: {device.upper()}")
    print(f"  ✅ Dimensions: {len(embeddings_result[0])}")
    print(f"  ✅ Embeddings working correctly")
    
    return True

def main():
    """Main entry point."""
    print_header("RAG MODULE TEST SUITE")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Project Root: {PROJECT_ROOT}")
    
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Setup: load modules and validate config (skip for embed-test which is standalone)
    if command != 'embed-test':
        if not setup():
            sys.exit(1)
    
    # Execute command
    if command == 'status':
        test_status()
    
    elif command == 'ingest':
        if len(sys.argv) < 3:
            print("Usage: python test_rag.py ingest <path>")
            sys.exit(1)
        test_ingest(sys.argv[2])
        test_status()
    
    elif command == 'retrieve':
        if len(sys.argv) < 3:
            print("Usage: python test_rag.py retrieve <query>")
            sys.exit(1)
        test_retrieve(' '.join(sys.argv[2:]))
    
    elif command == 'query':
        if len(sys.argv) < 3:
            print("Usage: python test_rag.py query <question>")
            sys.exit(1)
        test_query(' '.join(sys.argv[2:]))
    
    elif command == 'reset':
        test_reset()
    
    elif command == 'full':
        # Run a full test suite
        print_header("FULL TEST SUITE")
        
        test_status()
        
        if len(sys.argv) >= 3:
            # Ingest provided path
            test_ingest(sys.argv[2])
        
        # Test retrieval
        test_retrieve("What is this document about?")
        
        # Test query
        test_query("Summarize the main points of this document.")
    
    elif command == 'embed-test':
        # Test langchain_huggingface embeddings directly (skips ragbot)
        test_embeddings()
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)
    
    print_header("TEST COMPLETE")

if __name__ == '__main__':
    main()
