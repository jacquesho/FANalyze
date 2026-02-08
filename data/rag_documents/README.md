# RAG Test Documents

This directory contains small demo documents for the RAG (Retrieval-Augmented Generation) system.

## Documents

1. **`ticket_sales_strategies.pdf`**: intentionally fake ticket sales “strategies” (makes retrieval easy to validate).
2. **`musician_bios.pdf`**: intentionally fake musician bios (useful for verifying the app is pulling from documents, not general knowledge).

## Usage

These documents contain obviously fake information so it’s easy to tell when the app is using RAG results vs. general knowledge.

## Testing RAG Queries

Once processed, you can test RAG queries like:

- "What was Metallica's original genre?" (Should return: jazz fusion)
- "What time are tickets released?" (Should return: 3:33 AM on Friday the 13th)
- "What was Taylor Swift's first band?" (Should return: Swift Destruction, death metal)
- "How does weather affect ticket pricing?" (Should return: rain discounts for indoor shows)

These queries will help verify that the RAG system is correctly retrieving information from these documents.



