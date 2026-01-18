"""
Embedding generation and storage for RAG systems.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pinecone import Pinecone

logger = logging.getLogger(__name__)


class Embedder:
    """Handles embedding generation using Pinecone's built-in embedding model."""

    def __init__(self):
        """Initialize the embedder with Pinecone connection."""
        load_dotenv()
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")

        self.pc = Pinecone(api_key=api_key)
        logger.info("Initialized Pinecone embedder")

    def embed_chunks(
        self, chunks: list[dict[str, Any]], batch_size: int = 96
    ) -> list[list[float]]:
        """
        Generate embeddings for document chunks using Pinecone's built-in embedding model.

        Args:
            chunks: List of chunks with 'text' field
            batch_size: Number of texts to process per batch (default: 96, Pinecone limit)

        Returns:
            List of embedding vectors (each is a list of floats)
        """
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")

        # Extract text from chunks
        texts = [chunk["text"] for chunk in chunks]

        # Use Pinecone's built-in embedding (llama-text-embed-v2)
        # Model has a limit of 96 inputs per request, so we need to batch
        all_embeddings = []

        try:
            total_batches = (len(texts) + batch_size - 1) // batch_size
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i : i + batch_size]
                batch_num = i // batch_size + 1
                logger.info(
                    f"Processing batch {batch_num}/{total_batches} ({len(batch_texts)} texts)..."
                )

                response = self.pc.inference.embed(
                    model="llama-text-embed-v2",
                    inputs=batch_texts,
                    parameters={"input_type": "passage", "truncate": "END"},
                )

                batch_embeddings = [item.values for item in response.data]
                all_embeddings.extend(batch_embeddings)

            logger.info(
                f"Generated {len(all_embeddings)} embeddings with {len(all_embeddings[0])} dimensions"
            )
            return all_embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Search query text

        Returns:
            Embedding vector as list of floats
        """
        try:
            query_response = self.pc.inference.embed(
                model="llama-text-embed-v2",
                inputs=[query],
                parameters={"input_type": "query", "truncate": "END"},
            )
            return query_response.data[0].values
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise


def generate_embeddings_for_documents(
    document_paths: list[str],
    output_file: str = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[dict[str, Any]]:
    """
    Process documents and generate embeddings for all chunks.

    Args:
        document_paths: List of paths to PDF or text files
        output_file: Optional path to save embeddings JSON file
        chunk_size: Maximum tokens per chunk
        chunk_overlap: Token overlap between chunks

    Returns:
        List of chunks with embeddings and metadata
    """
    import sys

    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    from rag.document_processing import DocumentProcessor

    # Initialize processor
    processor = DocumentProcessor(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunking_strategy="token",
    )

    # Process all documents
    all_chunks = []
    for doc_path in document_paths:
        logger.info(f"Processing document: {doc_path}")
        chunks = processor.process_document(doc_path)
        all_chunks.extend(chunks)

    logger.info(f"Total chunks created: {len(all_chunks)}")

    # Generate embeddings
    embedder = Embedder()
    embeddings = embedder.embed_chunks(all_chunks)

    # Combine chunks with embeddings
    chunks_with_embeddings = []
    for chunk, embedding in zip(all_chunks, embeddings, strict=False):
        chunk_with_embedding = {
            "text": chunk["text"],
            "metadata": chunk["metadata"],
            "embedding": embedding,
        }
        chunks_with_embeddings.append(chunk_with_embedding)

    # Save to file if requested
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save without embeddings (too large for JSON) but include embedding dimensions
        chunks_for_save = []
        for chunk_data in chunks_with_embeddings:
            chunk_for_save = {
                "text": chunk_data["text"],
                "metadata": chunk_data["metadata"],
                "embedding_dimensions": len(chunk_data["embedding"]),
                "has_embedding": True,
            }
            chunks_for_save.append(chunk_for_save)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(chunks_for_save, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved chunk metadata to {output_path}")
        logger.info(
            "Note: Embeddings are generated in memory and ready for Pinecone storage"
        )

    return chunks_with_embeddings
