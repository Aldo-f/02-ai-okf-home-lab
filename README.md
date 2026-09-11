# AGENTS.md — OKF Home-Lab RAG System

## Purpose
This repository hosts the documentation bundle for the OKF Home-Lab Infrastructure. The RAG system indexes these docs and serves answers via API.

## Architecture
- **Bundle**: MkDocs site with multilingual support (EN/NL)
- **RAG Pipeline**: `rag/rag_query.py` — sentence-transformers + FAISS/Mem0
- **Query Classifier**: `rag/query_classifier.py` — gates greetings/off-topic
- **LLM Layer**: `rag/llm_answer.py` — freellm/auto for grounded answers
- **API**: `rag/rag_api.py` — FastAPI wrapper at `/search`

## Key Files
- `rag/query_classifier.py` — Query classification logic
- `rag/rag_query.py` — Main RAG pipeline
- `rag/llm_answer.py` — LLM answer generation
- `rag/rag_api.py` — FastAPI endpoints

## Configuration
- `.env`: `RAG_API_KEY` for API auth
- `mkdocs.en.yml`, `mkdocs.nl.yml`: Site build configs

## Testing
```bash
python3 -m pytest tests/rag/test_query_classifier.py -v
python3 -m pytest tests/api/test_rag_api.py -v
```

---

# Why the Deploy workflow is not needed

The `02-ai-okf-home-lab` repository only provides the **documentation bundle** that the RAG service indexes. The live chat widget lives on **`aldo-f.github.io`** and talks directly to **`rag.aldof.duckdns.org`**. Since the RAG server reads the bundle from the file system (or from the Docker volume) there is no requirement for a public GitHub‑Pages site for this repo.

Therefore:
- The MkDocs site built in the Deploy workflow was never consumed by the chatbot.
- Keeping the workflow only added CI noise (duplicate‑artifact error) and wasted build minutes.
- Removing it simplifies the CI pipeline and eliminates the deployment failure.

If you ever want a public docs view you can re‑add a similar workflow, but for the current architecture it is unnecessary.
