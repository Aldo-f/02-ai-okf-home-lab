#!/usr/bin/env python3
"""FastAPI wrapper around the OKF RAG pipeline.

POST /search with {"question": "...", "k": 3} returns {answer, sources, confidence}.
Run: uvicorn rag_api:app --host 0.0.0.0 --port 8000
(or ./scripts/run_rag_api.sh from the bundle root)
"""
import sys
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "rag"))

from rag_query import OKFRAGPipeline

app = FastAPI(title="OKF RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://aldo-f.github.io", "http://192.168.0.5:8001"],
    allow_methods=["POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

pipeline = OKFRAGPipeline(bundle_path=str(Path(__file__).resolve().parent.parent))


API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def get_api_key(api_key_header: str = Security(api_key_header)):
    if not api_key_header:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    expected_key = os.getenv("RAG_API_KEY")
    if not expected_key:
        raise HTTPException(status_code=500, detail="API key not configured on server")
    if api_key_header != expected_key:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    return api_key_header


class QueryPayload(BaseModel):
    question: str
    k: int = 3


@app.post("/search")
async def search(payload: QueryPayload, api_key: str = Security(get_api_key)):
    try:
        result = pipeline.query_with_answer(payload.question, k=payload.k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    try:
        from rag.chat_logger import log_chat
        log_chat(api_key, payload.question, result.get("answer",""), result.get("sources",[]), float(result.get("confidence", 0.0)), bool(result.get("llm_used", False)))
    except Exception:
        pass
    return result


@app.get("/health")
async def health():
    return {"status": "ok"}
