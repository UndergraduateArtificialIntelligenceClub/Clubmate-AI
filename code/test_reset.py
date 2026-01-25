"""
Quick test of db_reset() function.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_api import rag_ingest, rag_query, db_reset


def main():
    print("Testing db_reset() function...")
    print("=" * 60)
    
    # 1. Ingest a test file
    test_file = Path(__file__).parent / "test.pdf"
    if test_file.exists():
        print(f"\n1. Ingesting {test_file.name}...")
        success = rag_ingest(str(test_file))
        print(f"   {'✓' if success else '✗'} Ingestion {'succeeded' if success else 'failed'}")
    
    # 2. Try a query
    print("\n2. Testing query before reset...")
    try:
        result = rag_query("What is this about?")
        print(f"   ✓ Query returned {len(result['sources'])} sources")
    except Exception as e:
        print(f"   ✗ Query failed: {e}")
    
    # 3. Reset the database
    print("\n3. Resetting database...")
    success = db_reset()
    print(f"   {'✓' if success else '✗'} Reset {'succeeded' if success else 'failed'}")
    
    # 4. Try query after reset (should have no results)
    print("\n4. Testing query after reset...")
    try:
        result = rag_query("What is this about?")
        if len(result['sources']) == 0:
            print(f"   ✓ No sources found (database is empty)")
        else:
            print(f"   ⚠ Still found {len(result['sources'])} sources")
    except Exception as e:
        print(f"   ✗ Query failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ db_reset() test complete!")


if __name__ == "__main__":
    main()
