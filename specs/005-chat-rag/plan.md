# Plan: RAG Chat Widget Integration (005-chat-rag)

## Goal

Integrate the okf-home-lab RAG endpoint (`rag.aldof.duckdns.org/search`) into the
aldo-f.github.io documentation site via a floating chat widget, built by
`06-apps-aldo-f-github-io/hooks/chat.py` (MkDocs build hook), with zero key
exposure in shipped JavaScript.

## Steps (verified)

1. **Service restart** — `systemctl restart app-okf-rag` using the correct venv
   (`venv_rag/bin/python`) and `0.0.0.0:8000` bind (matches service template).
   ✅ Done: service `active (running)`, PID confirmed.

2. **RAG endpoint verification** — `curl -fsS -X POST http://127.0.0.1:8000/search
   -H "X-API-Key: $RAG_API_KEY" -d '{"question":"hello","k":1}'`
   ✅ Done: returns `{"answer":..., "sources":..., "confidence":...}` JSON.
   Note: "Unable to retrieve relevant information" returned for queries without
   matching docs in the bundle — correct behavior (bundle is the content corpus).

3. **Build EN** — `mkdocs build -f mkdocs.en.yml` via `venv/bin/python -m mkdocs`.
   ✅ Done: site built in 16.12s; chat.js emitted to `site/assets/javascripts/`.

4. **Build NL** — `mkdocs build -f mkdocs.nl.yml`.
   ✅ Done: site built; chat.js emitted to `site/nl/assets/javascripts/`.

5. **Key exposure check** — grep `RAG_API_KEY` and `aido_rag_` in both built
   `chat.js` files.
   ✅ Done: zero matches in both EN and NL builds.

6. **Widget JS injection check** — `hooks/chat.py` line 527:
   `js_path.write_text(_CHAT_JS, ...)` — no key substitution happens.
   The embedded `_CHAT_JS` string in `chat.py` contains no `RAG_API_KEY`.
   ✅ Verified.

7. **Widget test (browser)** — open local site, click chat button, send question,
   verify answer + sources render. (Pending — requires browser execution.)

8. **Write spec files** — `specs/005-chat-rag/spec.md` + `plan.md`.
   (This file, plus `spec.md` — written in the same commit.)

## Files Modified

| File | Change |
|------|--------|
| `06-apps-aldo-f-github-io/hooks/chat.py` | Existing; no changes needed (key-safe as-is) |
| `okf-home-lab/rag_api.py` | No changes; running via `app-okf-rag.service` |
| `01-core-infra/templates/systemd/app-okf-rag.service` | No changes; `venv_rag` interpreter + `0.0.0.0:8000` already correct |

## Files Created

| File | Purpose |
|------|--------|
| `okf-home-lab/specs/005-chat-rag/spec.md` | Feature spec |
| `okf-home-lab/specs/005-chat-rag/plan.md` | This plan |
