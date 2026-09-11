#!/usr/bin/env bash
# Full bootstrap for the OKF bundle + Hermes RAG integration on pi5.local
# Idempotent: safe to re-run at any time.

set -euo pipefail

BASE="$HOME/dev"
BUNDLE="$BASE/okf-home-lab"
SITE_REPO="$BASE/06-apps-aldo-f-github-io"

# pip extracts wheels into TMPDIR; /tmp is a small tmpfs on this Pi and
# torch's CUDA wheels blow it up. Point it at the real disk.
export TMPDIR="${TMPDIR:-$BUNDLE/.tmp}"
mkdir -p "$TMPDIR"

echo "=== Step 1 – create virtual environment (if missing) ==="
if [ ! -d "$BUNDLE/.venv" ]; then
  uv venv --link-mode=hardlink "$BUNDLE/.venv"
fi
source "$BUNDLE/.venv/bin/activate"

echo "=== Step 2 – install Python deps (CPU-only torch, RAG, faiss, yaml) ==="
uv pip install -U pip setuptools wheel
# CPU-only torch first, so sentence-transformers doesn't pull the
# multi-GB CUDA build (this is a Raspberry Pi — no NVIDIA GPU).
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install -r "$BUNDLE/rag/requirements.txt"

echo "=== Step 3 – build initial FAISS index (once) ==="
cd "$BUNDLE"
python - <<'PY'
import sys
sys.path.insert(0, 'rag')
from rag_query import OKFRAGPipeline
p = OKFRAGPipeline('.')
print(f"Indexed {p.index.ntotal if p.index is not None else 0} chunks")
PY

echo "=== Step 4 – register Hermes skill ==="
hermes skill add \\
  --name okf_rag_query \\
  --description "Query the OKF home-lab knowledge bundle (RAG)" \\
  --exec "$BUNDLE/rag/okf_rag_serve.py" \\
  --input-schema '{"type":"object","properties":{"question":{"type":"string"},"k":{"type":"integer"}},"required":["question"]}' \\
  --output-schema '{"type":"object","properties":{"answer":{"type":"string"},"confidence":{"type":"number"},"sources":{"type":"array","items":{"type":"object"}}},"required":["answer"]}' \\
  || echo "(skill already registered or hermes CLI unavailable – skipping)"

echo "=== Step 5 – install documentation watcher as user service ==="
SERVICE_FILE="$HOME/.config/systemd/user/okf-watcher.service"
mkdir -p "$(dirname "$SERVICE_FILE")"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=OKF documentation watcher - keeps bundle in sync
After=network-online.target

[Service]
ExecStart=$SITE_REPO/venv/bin/python $SITE_REPO/documentation_watcher/watcher.py --daemon
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now okf-watcher.service || true

echo "=== Step 6 – run the full test suite ==="
python "$BUNDLE/okf_test_suite.py"

echo "=== Step 7 – push updated docs to GitHub Pages ==="
cd "$SITE_REPO"
git add docs/en/okf-home-lab/
if git diff --cached --quiet; then
  echo "Nothing new to commit."
else
  git commit -m "Update OKF home-lab bundle (RAG integration)"
  git push origin main
fi

echo "OK: all done. Live site: https://aldo-f.github.io/okf-home-lab/"