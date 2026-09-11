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
