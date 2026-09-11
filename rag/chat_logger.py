import os, json, hashlib
from datetime import datetime, timezone

LOG_DIR = os.environ.get("CHAT_LOG_DIR", os.path.join(os.path.dirname(__file__), "..", "logs", "chat"))

def _user_id(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()[:12]

def log_chat(api_key: str, question: str, answer: str, sources: list, confidence: float, llm_ok: bool = False):
    os.makedirs(LOG_DIR, exist_ok=True)
    uid = _user_id(api_key)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "answer_preview": (answer or "")[:200],
        "sources": [s.get("title") for s in (sources or [])],
        "confidence": confidence,
        "llm_used": llm_ok,
    }
    path = os.path.join(LOG_DIR, f"{uid}.jsonl")
    try:
        with open(path, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass
