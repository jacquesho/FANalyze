#!/usr/bin/env python3
"""
Test the document retrieval system with hybrid search and reranking.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(dotenv_path=project_root / ".env")

# Fix Windows console encoding
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from rag.retrieval import DocumentRetriever

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_retrieval(query: str, use_hybrid: bool = True, use_reranking: bool = True):
    """Test document retrieval with a query."""
    print("\n" + "=" * 60)
    print("Document Retrieval Test")
    print("=" * 60)
    print(f"\nQuery: {query}")
    print(f"Hybrid search: {use_hybrid}")
    print(f"Reranking: {use_reranking}")

    try:
        # Use F2.0 index
        index_name = os.getenv("PINECONE_INDEX_NAME", "fanalyze-v2-rag")
        retriever = DocumentRetriever(index_name=index_name)
        results = retriever.search(
            query=query,
            top_k=10,
            use_hybrid=use_hybrid,
            use_reranking=use_reranking,
            rerank_top_k=5,
        )

        if results.get("error"):
            print(f"\n❌ Error: {results['error']}")
            return False

        print(f"\n✅ Found {results['total_results']} results")
        print(f"   Search method: {results['search_method']}")
        print(f"   Reranked: {results['reranked']}")

        print("\n" + "-" * 60)
        print("TOP RESULTS:")
        print("-" * 60)

        for i, result in enumerate(results["results"], 1):
            score = result.get("rerank_score") or result.get("similarity_score", 0)
            source = result.get("source", "Unknown")
            text = (
                result.get("text", "")[:300] + "..."
                if len(result.get("text", "")) > 300
                else result.get("text", "")
            )

            print(f"\n[{i}] Score: {score:.4f}")
            print(f"    Source: {source}")
            print(f"    Text: {text}")

        return True

    except Exception as e:
        print(f"\n❌ Error during retrieval: {e}")
        logger.exception("Full error details:")
        return False


if __name__ == "__main__":
    # Test queries
    test_queries = [
        "What was Metallica's original music genre?",
        "How does the inverted pricing model work?",
        "What is the midnight ticket release protocol?",
        "Tell me about Taylor Swift's early career",
    ]

    print("\n" + "=" * 60)
    print("Testing Document Retrieval System")
    print("=" * 60)

    # Test with hybrid search and reranking
    print("\n📊 TEST 1: Hybrid Search + Reranking")
    print("-" * 60)
    for query in test_queries[:2]:  # Test first 2 queries
        test_retrieval(query, use_hybrid=True, use_reranking=True)
        print("\n")

    # Test with dense-only and reranking
    print("\n📊 TEST 2: Dense-Only + Reranking")
    print("-" * 60)
    test_retrieval(test_queries[0], use_hybrid=False, use_reranking=True)

    print("\n" + "=" * 60)
    print("✅ Testing completed!")
    print("=" * 60)
