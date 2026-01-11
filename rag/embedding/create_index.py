#!/usr/bin/env python3
"""
Create Pinecone index for FANalyze v2.0 RAG system.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(dotenv_path=project_root / ".env")

# Fix Windows console encoding
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def create_index(index_name: str = "fanalyze-v2-rag", dimension: int = 1024):
    """
    Create a Pinecone index for FANalyze v2.0.

    Args:
        index_name: Name of the index to create
        dimension: Embedding dimension (1024 for llama-text-embed-v2)
    """
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("❌ Error: PINECONE_API_KEY environment variable is required")
        sys.exit(1)

    pc = Pinecone(api_key=api_key)

    print(f"\n🔧 Creating Pinecone index: {index_name}")
    print(f"   Dimension: {dimension}")
    print(f"   Model: llama-text-embed-v2")

    # Check if index already exists
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    if index_name in existing_indexes:
        print(f"\n⚠️  Index '{index_name}' already exists!")
        print("   Options:")
        print("   1. Use existing index (recommended if empty)")
        print("   2. Delete and recreate (will lose all data)")
        print("   3. Use a different name")
        return False

    try:
        # Create index with serverless spec (free tier)
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

        print(f"\n✅ Successfully created index: {index_name}")
        print(f"   Dimension: {dimension}")
        print(f"   Metric: cosine")
        print(f"   Cloud: AWS")
        print(f"   Region: us-east-1")
        print(f"\n💡 Add this to your .env file:")
        print(f"   PINECONE_INDEX_NAME={index_name}")

        return True

    except Exception as e:
        print(f"\n❌ Failed to create index: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create Pinecone index for FANalyze v2.0")
    parser.add_argument(
        "--index-name",
        "-i",
        default="fanalyze-v2-rag",
        help="Index name (default: fanalyze-v2-rag)",
    )
    parser.add_argument(
        "--dimension",
        "-d",
        type=int,
        default=1024,
        help="Embedding dimension (default: 1024 for llama-text-embed-v2)",
    )

    args = parser.parse_args()

    success = create_index(args.index_name, args.dimension)
    sys.exit(0 if success else 1)




