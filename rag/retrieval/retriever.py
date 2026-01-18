"""
Document retrieval with hybrid search and reranking.
"""

import logging
import os
from typing import Any

from dotenv import load_dotenv
from pinecone import Pinecone

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class DocumentRetriever:
    """Retrieves documents using hybrid search (dense + sparse) and reranking."""

    def __init__(self, index_name: str = None, namespace: str = "default"):
        """
        Initialize the document retriever.

        Args:
            index_name: Pinecone index name (defaults to PINECONE_INDEX_NAME env var)
            namespace: Pinecone namespace (default: 'default')
        """
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")

        self.index_name = index_name or os.getenv(
            "PINECONE_INDEX_NAME", "fanalyze-v2-rag"
        )
        if not self.index_name:
            raise ValueError(
                "Index name must be provided or PINECONE_INDEX_NAME must be set"
            )
        self.namespace = namespace
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(self.index_name)

        logger.info(
            f"Initialized DocumentRetriever with index: {self.index_name}, namespace: {self.namespace}"
        )

    def _generate_query_embedding(self, query: str) -> list[float]:
        """Generate dense embedding for query."""
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

    def _generate_sparse_vector(self, query: str) -> dict[str, Any]:
        """
        Generate sparse vector for keyword-based search using BM25-style approach.

        For hybrid search, Pinecone supports sparse vectors in the query.
        This implementation uses a simple term-frequency approach.
        In production, you might want to use a proper BM25 implementation or
        Pinecone's sparse embedding models if available.
        """
        try:
            # Try Pinecone's sparse embedding model (if available)
            sparse_response = self.pc.inference.embed(
                model="splade-v2",
                inputs=[query],
                parameters={"input_type": "query"},
            )
            # Sparse vectors are returned as indices and values
            return {
                "indices": sparse_response.data[0].indices,
                "values": sparse_response.data[0].values,
            }
        except Exception as e:
            # Fallback: For now, return None to use dense-only search
            # In a full implementation, you could use BM25 or other sparse vector methods
            logger.info(
                f"Sparse vector generation not available, using dense-only search: {e}"
            )
            return None

    def _rerank_results(
        self,
        query: str,
        results: list[dict[str, Any]],
        top_k: int = 5,
        model: str = "pinecone-rerank-v0",
    ) -> list[dict[str, Any]]:
        """
        Rerank search results using Pinecone's reranking model.

        Args:
            query: Original search query
            results: List of search results with 'text' and 'metadata'
            top_k: Number of top results to return after reranking
            model: Reranking model to use (default: pinecone-rerank-v0)

        Returns:
            Reranked list of results
        """
        if not results:
            return []

        try:
            # Prepare documents for reranking
            documents = [result["text"] for result in results]

            # Call Pinecone reranking API
            rerank_response = self.pc.inference.rerank(
                model=model,
                query=query,
                documents=documents,
                top_n=top_k,
            )

            # Handle different response formats
            if hasattr(rerank_response, "results") and rerank_response.results:
                # Map reranked results back to original results with scores
                reranked_results = []
                for rerank_item in rerank_response.results:
                    original_index = rerank_item.index
                    reranked_results.append(
                        {
                            **results[original_index],
                            "rerank_score": rerank_item.relevance_score,
                            "rerank_rank": rerank_item.rank + 1,  # 1-indexed
                        }
                    )
                logger.info(
                    f"Reranked {len(results)} results, returning top {len(reranked_results)}"
                )
                return reranked_results
            elif hasattr(rerank_response, "data") and rerank_response.data:
                # Alternative response format
                reranked_results = []
                for i, rerank_item in enumerate(rerank_response.data):
                    if i < len(results):
                        reranked_results.append(
                            {
                                **results[i],
                                "rerank_score": getattr(
                                    rerank_item, "relevance_score", 0
                                ),
                                "rerank_rank": i + 1,
                            }
                        )
                logger.info(
                    f"Reranked {len(results)} results, returning top {len(reranked_results)}"
                )
                return reranked_results
            else:
                logger.warning(
                    "Reranking response format not recognized, returning original results"
                )
                return results[:top_k]

        except Exception as e:
            logger.warning(f"Reranking failed (returning original results): {e}")
            # Fallback: return original results if reranking fails
            return results[:top_k]

    def search(
        self,
        query: str,
        top_k: int = 10,
        use_hybrid: bool = True,
        use_reranking: bool = True,
        rerank_top_k: int = 5,
        alpha: float = 0.7,
    ) -> dict[str, Any]:
        """
        Search documents using hybrid search and optional reranking.

        Args:
            query: Search query
            top_k: Number of results to retrieve initially (before reranking)
            use_hybrid: Whether to use hybrid search (dense + sparse)
            use_reranking: Whether to rerank results
            rerank_top_k: Number of results to return after reranking
            alpha: Weight for dense vs sparse (0.0 = sparse only, 1.0 = dense only, 0.7 = balanced)

        Returns:
            Dictionary with search results and metadata
        """
        logger.info(
            f"Searching for: '{query}' (hybrid={use_hybrid}, reranking={use_reranking})"
        )

        try:
            # Generate dense embedding
            dense_vector = self._generate_query_embedding(query)

            if use_hybrid:
                # Generate sparse vector for hybrid search
                sparse_vector = self._generate_sparse_vector(query)

                # Hybrid search: combine dense and sparse if available
                if sparse_vector and sparse_vector.get("indices"):
                    results = self.index.query(
                        vector=dense_vector,
                        sparse_vector=sparse_vector,
                        top_k=top_k,
                        include_metadata=True,
                        namespace=self.namespace,
                        alpha=alpha,  # Weight: 0.7 = 70% dense, 30% sparse
                    )
                    logger.info(
                        f"Using hybrid search (dense + sparse) with alpha={alpha}"
                    )
                else:
                    # Fallback to dense-only if sparse generation not available
                    logger.info(
                        "Sparse vectors not available, using dense-only search (still effective)"
                    )
                    results = self.index.query(
                        vector=dense_vector,
                        top_k=top_k,
                        include_metadata=True,
                        namespace=self.namespace,
                    )
            else:
                # Dense-only search
                results = self.index.query(
                    vector=dense_vector,
                    top_k=top_k,
                    include_metadata=True,
                    namespace=self.namespace,
                )

            if not results.matches:
                return {
                    "query": query,
                    "total_results": 0,
                    "results": [],
                    "search_method": "hybrid" if use_hybrid else "dense",
                    "reranked": False,
                    "message": f"No documents found matching your query: '{query}'",
                }

            # Format initial results
            formatted_results = []
            for match in results.matches:
                formatted_results.append(
                    {
                        "chunk_id": match.id,
                        "text": match.metadata.get("text", ""),
                        "source": match.metadata.get("source", "Unknown"),
                        "similarity_score": round(match.score, 4),
                        "metadata": {
                            k: v for k, v in match.metadata.items() if k != "text"
                        },
                    }
                )

            # Apply reranking if requested
            if use_reranking and len(formatted_results) > 1:
                logger.info(f"Reranking {len(formatted_results)} results...")
                reranked_results = self._rerank_results(
                    query, formatted_results, top_k=rerank_top_k
                )
                final_results = reranked_results
                reranked = True
            else:
                final_results = (
                    formatted_results[:rerank_top_k]
                    if use_reranking
                    else formatted_results
                )
                reranked = False

            logger.info(f"Found {len(final_results)} relevant document chunks")

            return {
                "query": query,
                "total_results": len(final_results),
                "results": final_results,
                "search_method": "hybrid" if use_hybrid else "dense",
                "reranked": reranked,
                "index_name": self.index_name,
                "namespace": self.namespace,
            }

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                "query": query,
                "total_results": 0,
                "results": [],
                "error": str(e),
                "search_method": "hybrid" if use_hybrid else "dense",
                "reranked": False,
            }


def search_documents(
    query: str,
    top_k: int = 10,
    use_hybrid: bool = True,
    use_reranking: bool = True,
    rerank_top_k: int = 5,
) -> dict[str, Any]:
    """
    Convenience function to search documents.

    Args:
        query: Search query
        top_k: Number of results to retrieve initially
        use_hybrid: Whether to use hybrid search
        use_reranking: Whether to rerank results
        rerank_top_k: Number of results after reranking

    Returns:
        Search results dictionary
    """
    retriever = DocumentRetriever()
    return retriever.search(
        query=query,
        top_k=top_k,
        use_hybrid=use_hybrid,
        use_reranking=use_reranking,
        rerank_top_k=rerank_top_k,
    )
