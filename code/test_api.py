"""
Test script for RAG API.

Quick test to verify the API is working correctly.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_api import rag_ingest, rag_query


def test_basic_functionality():
    """Test basic ingestion and query."""
    
    print("Testing RAG API...")
    print()
    
    # Check environment
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ GOOGLE_API_KEY not set")
        print("Set it with: export GOOGLE_API_KEY='your-key'")
        return False
    
    print("✓ GOOGLE_API_KEY is set")
    
    # Test import
    try:
        from rag_api import rag_ingest, rag_query
        print("✓ Successfully imported rag_ingest and rag_query")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test ingestion (using test.pdf)
    test_file = Path(__file__).parent / "test.pdf"
    
    if not test_file.exists():
        print(f"❌ test.pdf not found at: {test_file}")
        return False
    
    print(f"\n📄 Testing ingestion with: {test_file}")
    
    try:
        success = rag_ingest(str(test_file))
        if success:
            print("✓ Ingestion successful")
        else:
            print("⚠️  Ingestion returned False")
            return False
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test query - ask about the PDF content
    print("\n❓ Testing query...")
    test_question = "What is this document about?"
    
    try:
        result = rag_query(test_question)
        print(f"✓ Query successful")
        print(f"   Question: {test_question}")
        print(f"   Answer: {result['generation'][:100]}...")
        print(f"   Sources: {len(result['sources'])} documents")
        if result['sources']:
            print(f"   Top source: {result['sources'][0]['source']} (score: {result['sources'][0]['relevance_score']:.4f})")
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
