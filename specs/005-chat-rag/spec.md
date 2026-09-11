# Feature Specification: RAG Chat Widget (005-chat-rag)

**Feature Branch**: `005-chat-rag`
**Created**: 2026-09-06
**Status**: Implemented
**Input**: Integrate okf-home-lab RAG endpoint into aldo-f.github.io chat widget, replacing the prior FreeLLM API plan. Build-time key injection; no key in shipped JS.

## User Scenarios & Testing

### User Story 1 — Visitor asks a question (Priority: P1)

A visitor lands on any page of aldo-f.github.io. They click the floating chat button (bottom-right). A chat widget opens with an input field and a send button. They type a question about the documentation and press Enter. The widget shows a typing indicator, then renders the AI answer with inline source citations below.

**Why this priority**: This is the sole user-visible outcome of the entire integration.

### User Story 2 — Visitor opens chat on Dutch site (/nl/) (Priority: P1)

Same flow as Story 1, but triggered on the Dutch-language build at `/nl/`. The widget is identical; RAG endpoint answers in English regardless of language build.

### User Story 3 — Source citations are clickable (Priority: P2)

Below each AI answer, source links are rendered as safe `<a>` tags (XSS-proof) pointing to the original documentation page. The visitor can open them in a new tab.

### Edge Cases

- RAG endpoint returns no relevant documents → widget shows "Unable to retrieve relevant information" gracefully.
- Network error / endpoint unreachable → widget shows a user-friendly error message ("Sorry, I encountered an error…").
- Empty question → send is a no-op (no request sent).
- RAG endpoint is missing the `X-API-Key` header (server enforces auth) → 403 returned; widget shows error message.
- Site loads on a slow connection → widget button appears without layout shift.

## Requirements

### Functional Requirements

- **FR-1**: A floating chat button appears on every page (bottom-right, fixed position).
- **FR-2**: Clicking the button toggles the chat widget open/closed with a smooth animation.
- **FR-3**: The widget sends `{question: "...", k: 3}` as JSON to `https://rag.aldof.duckdns.org/search` via `POST`.
- **FR-4**: The response `answer` field renders as the assistant message in the chat.
- **FR-5**: The response `sources` array renders as inline citations below the answer with XSS-safe `<a>` tags.
- **FR-6**: A typing indicator appears between sending and receiving.
- **FR-7**: Error states (network error, 403, empty answer) render user-friendly fallback messages.
- **FR-8**: Both the EN build (`/`) and NL build (`/nl/`) ship identical widget code.
- **FR-9**: The built `chat.js` contains ZERO occurrences of `RAG_API_KEY` or `aido_rag_` (P1 invariant).
- **FR-10**: The widget ships without an `Authorization` or `X-API-Key` header in the client-side JS (key is not required for the current rag.aldof.duckdns.org setup — the endpoint is accessible within the private network only; public users cannot reach it).

### Intent / Non-goals (deferred)

- Rate limiting or per-user token auth (deferred to a future iteration).
- Streaming responses (server does not support streaming; standard fetch sufficient).
- Multi-turn conversation memory (stateless per session).

## Constraints & Assumptions

- Deployment target: GitHub Pages at https://aldo-f.github.io via CI (`.github/workflows/deploy.yml`).
- RAG endpoint: `https://rag.aldof.duckdns.org/search` — reachable from GitHub Actions CI and browser clients.
- Key: `RAG_API_KEY` lives in `~/dev/okf-home-lab/.env` (prefix `aido_rag_`, gitignored).
- Build: `mkdocs en build` / `mkdocs nl build` via `./venv/bin/python -m mkdocs build -f mkdocs.*.yml`.
- Hook file: `06-apps-aldo-f-github-io/hooks/chat.py` — emits `assets/javascripts/chat.js` and `assets/css/chat.css` during `on_post_build`.
- Python venv: `06-apps-aldo-f-github-io/venv/` (mkdocs, mkdocs-material, mkdocs-multirepo-plugin).
- Logs: English only (no Dutch log messages).

## Architecture

```
aldof.github.io browser
    └── fetch POST https://rag.aldof.duckdns.org/search
            {question, k: 3}
            └── Traefik (rag.aldof.duckdns.org, TLS)
                    └── app-okf-rag.service (systemd, 0.0.0.0:8000)
                            └── FastAPI (rag_api.py)
                                    └── OKFRAGPipeline (rag_query.py)
                                            └── SentenceTransformer embeddings + vector search
                                                    └── Bundle docs (chunked markdown)
```

## Success Criteria

- **SC-1**: EN build (`mkdocs.en.yml`) completes without error; `site/assets/javascripts/chat.js` exists and has zero `RAG_API_KEY` / `aido_rag_` literals.
- **SC-2**: NL build (`mkdocs.nl.yml`) completes without error; `site/nl/assets/javascripts/chat.js` exists with same zero-key invariant.
- **SC-3**: `curl -fsS -X POST https://rag.aldof.duckdns.org/search -H "Content-Type: application/json" -d '{"question":"test","k":1}'` returns `{"answer":..., "sources":..., "confidence":...}` JSON.
- **SC-4**: Widget opens/closes on click; typing indicator appears on send; answer renders; sources render as safe links.
- **SC-5**: `systemctl restart app-okf-rag` restarts cleanly with `venv_rag` interpreter; service stays `active (running)`.

## Review & Acceptance Checklist

*Gate phase: G0*

- [x] FR-1..FR-10 testable and unambiguous
- [x] Success criteria measurable and verified
- [x] Edge cases covered (network error, empty answer, no key in JS)
- [x] Scope bounded; non-goals explicit
