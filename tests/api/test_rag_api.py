import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

BUNDLE = Path(__file__).resolve().parents[2]
URL = "http://127.0.0.1:8000/search"


def _load_api_key() -> str | None:
    """Load RAG_API_KEY from .env (local) or env (CI)."""
    key = os.getenv("RAG_API_KEY")
    if key:
        return key
    env_path = BUNDLE / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("RAG_API_KEY="):
            return line.split("=", 1)[1].strip().strip("\"'")
    return None


def _server_running() -> bool:
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:8000/openapi.json", timeout=2)
        return True
    except Exception:
        return False


def test_search_endpoint():
    api_key = _load_api_key()
    if not api_key:
        pytest.skip("RAG_API_KEY not configured; skipping auth-required test")

    if not _server_running():
        env = os.environ.copy()
        env["RAG_API_KEY"] = api_key
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "rag_api:app",
             "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(BUNDLE / "rag"),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env=env,
        )
        for _ in range(60):
            if _server_running():
                break
            time.sleep(1)
        else:
            proc.terminate()
            raise RuntimeError("RAG API did not start within 60s")

    headers = {"X-API-Key": api_key}
    response = requests.post(
        URL,
        json={"question": "How to enable Jellyfin hardware transcoding?"},
        headers=headers,
        timeout=120,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "answer" in data and "sources" in data
