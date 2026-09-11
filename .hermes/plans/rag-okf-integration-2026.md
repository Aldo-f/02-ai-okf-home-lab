# /goal: RAG okf-home-lab integration with aldo-f-github-io

## Source evidence
- `/home/aldo/dev/okf-home-lab/plan` (FreeLLM chat widget plan for aldo-f.github.io)
- `/home/aldo/dev/okf-home-lab/docs/root/PLAN_OKF_RAG_AGENTS.md` (RAG agent plan)
- Hooks file: `/home/aldo/dev/06-apps-aldo-f-github-io/hooks/chat.py` (calls rag.aldof.duckdns.org/search)
- RAG dir: `/home/aldo/dev/okf-home-lab/rag/` + `.specify/integrations/`

## Goal
Integrate RAG service of `okf-home-lab` into `aldo-f-github-io` documentation site (chat widget / search endpoint), using build-time injection of RAG_API_KEY (hidden from client JS) and verified endpoint `https://rag.aldof.duckdns.org/search`.

## Steps (verifiable)
1. Read current `plan` and `PLAN_OKF_RAG_AGENTS.md`
2. Confirm RAG endpoint reachable (curl rag.aldof.duckdns.org/search or check `rag_api.pid`)
3. Modify `06-apps-aldo-f-github-io/hooks/chat.py`: keep endpoint / key injection, verify no exposed secret in emitted JS
4. Build `mkdocs.en.yml` / `mkdocs.nl.yml`; verify `chat.js` emitted with build-time key (not hardcoded)
5. Test locally (`python -m http.server` or `mkdocs serve`); confirm widget opens, sends, receives answer with sources
6. Confirm `.specify/` spec matches (check `specs/` or `.specify/templates/` if defined)
7. Report: endpoint working yes/no, key exposure none, site builds both languages

## Constraints
- RAG_API_KEY never in client JS (P1 fix already in chat.py comment); keep that
- Build for both EN (`mkdocs.en.yml`) and NL (`mkdocs.nl.yml`)
- Confirm before destructive edits to hooks/chat.py
