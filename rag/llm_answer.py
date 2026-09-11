# LLM answer layer — uses freellm/auto at https://freellm.aldof.duckdns.org/v1
# Secrets via env (FREELLM_API_KEY); openai-compatible /v1/chat/completions

def _generate_answer(sources_text: str, question: str, api_key: str = None) -> str:
    import os, urllib.request, json
    key = api_key or os.environ.get("FREELLM_API_KEY") or os.environ.get("RAG_API_KEY")
    if not key:
        return f"Based on the documentation:\n\n{sources_text}"
    payload = json.dumps({
        "model": "auto",
        "messages": [{"role":"system","content":"Answer briefly using only the provided docs."},{"role":"user","content":f"Question: {question}\nSources:\n{sources_text}"}],
        "temperature": 0.3,
        "max_tokens": 400,
    }).encode()
    req = urllib.request.Request("https://freellm.aldof.duckdns.org/v1/chat/completions",
        data=payload, headers={"Content-Type":"application/json","Authorization":f"Bearer {key}"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        try:
            _log_llm_failure(question, str(e))
        except Exception:
            pass
        return f"Based on the documentation:\n\n{sources_text}\n\n(LLM unavailable: {e})"

def _log_llm_failure(question: str, error: str):
    try:
        import os
        log_dir = os.path.join(os.path.dirname(__file__), "..", "logs", "chat")
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "llm_failures.jsonl"), "a") as f:
            f.write(json.dumps({"ts": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(), "question": question, "error": str(error)}, ensure_ascii=False) + "\n")
    except Exception:
        pass
