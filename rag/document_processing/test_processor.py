#!/usr/bin/env python3
"""
Simple test script for document processing pipeline.
Run this to verify document processing is working correctly.
"""

import json
import logging
import sys
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(dotenv_path=project_root / ".env")

from rag.document_processing import DocumentProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_document_processing(file_path: str):
    """Test document processing with a sample file."""
    print("\n" + "=" * 60)
    print("Testing Document Processing Pipeline")
    print("=" * 60)
    
    if not Path(file_path).exists():
        print(f"❌ Error: File '{file_path}' not found.")
        return False
    
    try:
        # Initialize processor with token-based chunking
        processor = DocumentProcessor(
            chunk_size=1000,  # 1000 tokens
            chunk_overlap=200,  # 200 tokens overlap
            chunking_strategy="token",
        )
        
        print(f"\n📄 Processing: {file_path}")
        print(f"   Strategy: Token-based chunking")
        print(f"   Chunk size: 1000 tokens")
        print(f"   Overlap: 200 tokens\n")
        
        # Process document
        chunks = processor.process_document(file_path)
        
        if not chunks:
            print("❌ No chunks were created. Check the document and try again.")
            return False
        
        # Display results
        print(f"\n✅ Successfully processed document!")
        print(f"   Created {len(chunks)} chunks\n")
        
        # Show first chunk as example
        if chunks:
            first_chunk = chunks[0]
            print("=" * 60)
            print("EXAMPLE CHUNK (First chunk):")
            print("=" * 60)
            print(f"Source: {first_chunk['metadata']['source']}")
            print(f"Chunk {first_chunk['metadata']['chunk_index'] + 1}/{first_chunk['metadata']['total_chunks']}")
            print(f"Size: {first_chunk['metadata']['chunk_size']} chars, {first_chunk['metadata']['chunk_size_tokens']} tokens")
            print(f"Strategy: {first_chunk['metadata']['chunking_strategy']}")
            print("-" * 60)
            print(first_chunk['text'][:500] + "..." if len(first_chunk['text']) > 500 else first_chunk['text'])
            print("-" * 60)
        
        # Show statistics
        stats = processor.get_processing_stats(chunks)
        print("\n" + "=" * 60)
        print("PROCESSING STATISTICS")
        print("=" * 60)
        print(f"Total chunks: {stats['total_chunks']}")
        print(f"Average chunk size: {stats['avg_chunk_size']:.1f} characters")
        print(f"Chunk size range: {stats['min_chunk_size']} - {stats['max_chunk_size']} characters")
        print(f"Average token count: {stats['avg_token_count']:.1f} tokens")
        print(f"Token count range: {stats['min_token_count']} - {stats['max_token_count']} tokens")
        print(f"Sources processed: {len(stats['sources'])}")
        for source in stats['sources']:
            print(f"  - {source}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        logger.exception("Full error details:")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_processor.py <path_to_document>")
        print("\nExample:")
        print("  python test_processor.py sample_documents/test.pdf")
        print("  python test_processor.py sample_documents/test.txt")
        sys.exit(1)
    
    file_path = sys.argv[1]
    success = test_document_processing(file_path)
    sys.exit(0 if success else 1)

