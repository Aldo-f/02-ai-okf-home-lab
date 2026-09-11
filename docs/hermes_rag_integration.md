# Hermes RAG Integration Spec

Hermes can now query `https://rag.aldof.duckdns.org/search` (local Pi5 via Traefik) using `RAG_API_KEY` from `.env`. Implementation: use `requests` (or `urllib`) with the key injected from `~/dev/okf-home-lab/.env`.
