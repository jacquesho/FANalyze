"""
Document retrieval module for RAG systems.
Implements hybrid search (dense + sparse) and reranking.
"""

from .retriever import DocumentRetriever, search_documents

__all__ = ["DocumentRetriever", "search_documents"]
