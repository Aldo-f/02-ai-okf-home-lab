#!/usr/bin/env python3
"""Hermes RAG query tool: read .env, POST to rag.aldof.duckdns.org/search."""
import os, json, sys, urllib.request
from pathlib import Path

RAG_URL = os.environ.get("RAG_URL", "https://rag.aldof.duckdns.org/search")
ENV_PATH = Path("/home/aldo/dev/okf-home-lab/.env")

def _load_key() -> str:
    if not ENV_PATH.exists():
        sys.exit("RAG_API_KEY missing — .env not found at " + str(ENV_PATH))
    for line in ENV_PATH.read_text().splitlines():
        if line.startswith("RAG_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("RAG_API_KEY not set in " + str(ENV_PATH))

def query(question: str, k: int = 3) -> dict:
    key = _load_key()
    req = urllib.request.Request(
        RAG_URL,
        data=json.dumps({"question": question, "k": k}).encode(),
        headers={"Content-Type": "application/json", "X-API-Key": key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "What is OKF?"
    result = query(q)
    print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
