## Automatic Document Indexing

All markdown files inside this bundle are automatically discovered by
`OKFRAGPipeline` (it walks the bundle root with `rglob("*.md")`). No additional
configuration is required — simply add or modify a `.md` file and the next
query will include the new content.

## Vector store selection

The pipeline reads `hermes config get memory.provider` at startup:

- `mem0` → documents are indexed into the Mem0 Platform (`collection="okf_rag"`,
  requires `MEM0_API_KEY` in the environment or `~/.hermes/.env`). Search runs
  server-side via `rag/mem0_store.py`.
- anything else (or if the config call fails) → local FAISS index as before.
