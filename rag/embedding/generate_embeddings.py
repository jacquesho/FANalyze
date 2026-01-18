#!/usr/bin/env python3
"""
Generate embeddings for document chunks.
Processes PDFs, generates embeddings, and optionally stores them in Pinecone.
"""

import json
import logging
import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(dotenv_path=project_root / ".env")

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from rag.document_processing import DocumentProcessor
from rag.embedding import Embedder

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--documents",
    "-d",
    multiple=True,
    required=True,
    help="Path(s) to PDF or text documents to process",
)
@click.option(
    "--chunk-size",
    "-s",
    default=1000,
    help="Maximum tokens per chunk (default: 1000)",
)
@click.option(
    "--chunk-overlap",
    "-o",
    default=200,
    help="Token overlap between chunks (default: 200)",
)
@click.option(
    "--output",
    "-out",
    type=click.Path(),
    help="Save chunk metadata to JSON file (embeddings generated in memory)",
)
@click.option(
    "--store-pinecone",
    is_flag=True,
    help="Store embeddings in Pinecone index",
)
@click.option(
    "--index-name",
    "-i",
    default=None,
    help="Pinecone index name (defaults to PINECONE_INDEX_NAME env var)",
)
@click.option(
    "--namespace",
    "-n",
    default="default",
    help="Pinecone namespace (default: 'default')",
)
def main(
    documents: tuple[str, ...],
    chunk_size: int,
    chunk_overlap: int,
    output: str,
    store_pinecone: bool,
    index_name: str,
    namespace: str,
):
    """
    Generate embeddings for document chunks.

    Processes PDFs or text files, generates embeddings using Pinecone's built-in
    embedding model, and optionally stores them in Pinecone for RAG retrieval.
    """
    print("\n" + "=" * 60)
    print("Document Embedding Generation")
    print("=" * 60)

    # Validate documents exist
    document_paths = []
    for doc in documents:
        doc_path = Path(doc)
        if not doc_path.exists():
            print(f"❌ Error: Document '{doc}' not found.")
            sys.exit(1)
        document_paths.append(str(doc_path))

    try:
        # Initialize processor
        print(f"\n📄 Processing {len(document_paths)} document(s)...")
        processor = DocumentProcessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunking_strategy="token",
        )

        # Process all documents
        all_chunks = []
        for doc_path in document_paths:
            print(f"  Processing: {doc_path}")
            chunks = processor.process_document(doc_path)
            all_chunks.extend(chunks)
            print(f"    Created {len(chunks)} chunks")

        print(f"\n✅ Total chunks created: {len(all_chunks)}")

        # Generate embeddings
        print("\n🧠 Generating embeddings...")
        embedder = Embedder()
        embeddings = embedder.embed_chunks(all_chunks)

        print(f"✅ Generated {len(embeddings)} embeddings")
        print(f"   Embedding dimensions: {len(embeddings[0])}")

        # Store in Pinecone if requested
        if store_pinecone:
            print("\n📦 Storing embeddings in Pinecone...")
            index_name = index_name or os.getenv("PINECONE_INDEX_NAME")
            if not index_name:
                print(
                    "❌ Error: PINECONE_INDEX_NAME environment variable required for Pinecone storage"
                )
                sys.exit(1)

            try:
                index = embedder.pc.Index(index_name)
                print(f"✅ Connected to Pinecone index: {index_name}")

                # Prepare vectors for upsert
                vectors = []
                for i, (chunk, embedding) in enumerate(
                    zip(all_chunks, embeddings, strict=False)
                ):
                    # Create unique ID from source and chunk index
                    source_name = Path(chunk["metadata"]["source"]).stem
                    vector_id = (
                        f"{source_name}_chunk_{chunk['metadata']['chunk_index']}"
                    )

                    vector = {
                        "id": vector_id,
                        "values": embedding,
                        "metadata": {
                            **chunk["metadata"],
                            "text": chunk["text"][
                                :1000
                            ],  # Limit text length for metadata
                        },
                    }
                    vectors.append(vector)

                # Upsert to Pinecone (batch in chunks of 100)
                batch_size = 100
                total_batches = (len(vectors) + batch_size - 1) // batch_size
                for i in range(0, len(vectors), batch_size):
                    batch = vectors[i : i + batch_size]
                    batch_num = i // batch_size + 1
                    index.upsert(vectors=batch, namespace=namespace)
                    print(
                        f"  Stored batch {batch_num}/{total_batches} ({len(batch)} vectors)"
                    )

                print(
                    f"✅ Successfully stored {len(vectors)} vectors in namespace '{namespace}'"
                )

                # Get index stats
                stats = index.describe_index_stats()
                print("\n📊 Index Statistics:")
                print(f"   Total vectors: {stats.total_vector_count}")
                print(f"   Dimension: {stats.dimension}")
                print(f"   Namespaces: {list(stats.namespaces.keys())}")

            except Exception as e:
                print(f"❌ Failed to store in Pinecone: {e}")
                logger.exception("Full error details:")
                sys.exit(1)

        # Save metadata to file if requested
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save chunk metadata (without embeddings - too large)
            chunks_for_save = []
            for chunk_data, embedding in zip(all_chunks, embeddings, strict=False):
                chunk_for_save = {
                    "text": chunk_data["text"],
                    "metadata": chunk_data["metadata"],
                    "embedding_dimensions": len(embedding),
                    "has_embedding": True,
                }
                chunks_for_save.append(chunk_for_save)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(chunks_for_save, f, indent=2, ensure_ascii=False)

            print(f"\n💾 Saved chunk metadata to: {output_path}")
            print("   Note: Embeddings are in memory and ready for Pinecone storage")

        print("\n" + "=" * 60)
        print("✅ Embedding generation completed successfully!")
        print("=" * 60)
        if store_pinecone:
            print(f"🎯 Embeddings stored in Pinecone index: {index_name}")
            print(f"🎯 Namespace: {namespace}")
            print("🎯 Ready for RAG retrieval!")

    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        logger.exception("Full error details:")
        sys.exit(1)


if __name__ == "__main__":
    main()
