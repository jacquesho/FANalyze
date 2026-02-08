# Data

This repo keeps **small, non-sensitive** sample inputs under `data/` to make demos repeatable without committing secrets.

## Structure

```
data/
├── external/staging_json/   # JSONL show snapshots (batch input examples)
└── rag_documents/           # Small demo PDFs used for RAG
```

## Notes
- Don’t commit credentials or private keys here (use `.secrets/` + `.env` locally).
- If you add large datasets, prefer generating them via scripts instead of committing them.
