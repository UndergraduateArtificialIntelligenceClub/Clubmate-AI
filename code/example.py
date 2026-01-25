"""
Example usage of the RAG API.

This script demonstrates how to use rag_ingest() and rag_query() in your application.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path so we can import rag_api
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_api import rag_ingest, rag_query


def main():
    """Example RAG API usage."""
    
    print("=" * 80)
    print("RAG API Example")
    print("=" * 80)
    
    # Ensure API key is set
    if not os.getenv('GOOGLE_API_KEY'):
        print("\n⚠️  GOOGLE_API_KEY not set!")
        print("Please set it in .env or export it:")
        print("  export GOOGLE_API_KEY='your-key-here'")
        return
    
    # Example 1: Ingest a single file
    print("\n📄 Example 1: Ingest a single file")
    print("-" * 80)
    
    test_file = "data/documents/info.md"  # Adjust path as needed
    if Path(test_file).exists():
        print(f"Ingesting: {test_file}")
        success = rag_ingest(test_file)
        print(f"Result: {'✓ Success' if success else '✗ Failed'}")
    else:
        print(f"⚠️  File not found: {test_file}")
    
    # Example 2: Ingest a directory
    print("\n📁 Example 2: Ingest a directory")
    print("-" * 80)
    
    test_dir = "data/documents"
    if Path(test_dir).exists():
        print(f"Ingesting directory: {test_dir}")
        success = rag_ingest(test_dir)
        print(f"Result: {'✓ Success' if success else '✗ Failed'}")
    else:
        print(f"⚠️  Directory not found: {test_dir}")
    
    # Example 3: Simple query
    print("\n❓ Example 3: Simple query")
    print("-" * 80)
    
    question = "What is this document about?"
    print(f"Question: {question}")
    print()
    
    try:
        result = rag_query(question)
        print(f"Answer: {result['generation']}")
        print(f"\nSources ({len(result['sources'])}):")
        for i, source in enumerate(result['sources'], 1):
            pages = f", pages {source.get('pages', [])}" if source.get('pages') else ""
            print(f"  {i}. {source['source']} (score: {source['relevance_score']:.4f}){pages}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 4: Query with custom parameters
    print("\n❓ Example 4: Query with custom parameters")
    print("-" * 80)
    
    question = "What are the key points?"
    print(f"Question: {question}")
    print(f"Parameters: top_k=10, llm=gemini-2.5-flash-lite")
    print()
    
    try:
        result = rag_query(
            question,
            topk_results=10,
            llm="gemini-2.5-flash-lite"
        )
        print(f"Answer: {result['generation']}")
        print(f"Sources: {len(result['sources'])} documents")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 5: Multiple questions
    print("\n❓ Example 5: Multiple questions")
    print("-" * 80)
    
    questions = [
        "What is the main topic?",
        "What recommendations are made?",
        "What are the conclusions?"
    ]
    
    for i, q in enumerate(questions, 1):
        print(f"\n{i}. {q}")
        try:
            result = rag_query(q)
            print(f"   → {result['generation'][:200]}...")  # Show first 200 chars
        except Exception as e:
            print(f"   → Error: {e}")
    
    print("\n" + "=" * 80)
    print("Example complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
