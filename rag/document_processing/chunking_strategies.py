"""
Chunking strategies for document processing.
"""

import logging

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class ChunkingStrategy:
    """Base class for chunking strategies."""

    def chunk(self, text: str, **kwargs) -> list[str]:
        """Split text into chunks."""
        raise NotImplementedError


class TokenBasedChunking(ChunkingStrategy):
    """Token-based chunking using tiktoken for OpenAI models."""

    def chunk(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200,
        model: str = "text-embedding-3-small",
    ) -> list[str]:
        """
        Split text into chunks based on token count.

        Args:
            text: Input text to chunk
            chunk_size: Maximum tokens per chunk
            overlap: Number of tokens to overlap between chunks
            model: OpenAI model name for tokenizer

        Returns:
            List of text chunks
        """
        try:
            # Initialize tiktoken encoder
            encoder = tiktoken.encoding_for_model(model)

            # Define length function based on token count
            def length_function(txt: str) -> int:
                return len(encoder.encode(txt))

            # Use RecursiveCharacterTextSplitter with token-based length function
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
                length_function=length_function,
                separators=["\n\n", "\n", " ", ""],
            )

            chunks = text_splitter.split_text(text)

            logger.info(f"Created {len(chunks)} chunks using token-based chunking")
            return chunks

        except Exception as e:
            logger.error(f"Error in token-based chunking: {e}")
            raise


def get_chunking_strategy(strategy_name: str) -> ChunkingStrategy:
    """Get a chunking strategy by name."""
    strategies = {
        "token": TokenBasedChunking(),
    }

    if strategy_name not in strategies:
        raise ValueError(f"Unknown chunking strategy: {strategy_name}. Available: {list(strategies.keys())}")

    return strategies[strategy_name]


def chunk_text(text: str, strategy: str = "token", **kwargs) -> list[str]:
    """
    Chunk text using the specified strategy.

    Args:
        text: Input text to chunk
        strategy: Chunking strategy name
        **kwargs: Additional arguments for the chunking strategy

    Returns:
        List of text chunks
    """
    chunker = get_chunking_strategy(strategy)
    return chunker.chunk(text, **kwargs)



