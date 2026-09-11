# Pi 5 / ARM64 dependency pins for the OKF RAG pipeline

Verified on pi5.local (Raspberry Pi 5, Debian, Python 3.13).

## Known-good `rag/requirements.txt`

```
sentence-transformers==2.2.2
faiss-cpu==1.9.0.post1
numpy==1.26.4
PyYAML
```

## Why each pin

| Package | Pin | Reason |
|---|---|---|
| numpy | >= 1.26.4 | `numpy==1.24.x` sdist fails to build on Python 3.13: `AttributeError: module 'pkgutil' has no attribute 'ImpImporter'` during `get_requires_for_build_wheel`. |
| faiss-cpu | == 1.9.0.post1 | Older pins (1.7.x) have no aarch64 / cp313 wheel on PyPI/piwheels; pip errors with "No matching distribution". 1.9.0.post1 ships a `cp313 manylinux_2_17_aarch64` wheel. |
| sentence-transformers | == 2.2.2 | Works with the above; pulls torch (large download — expect a long install on the Pi). |

## FAISS fallback

If faiss cannot be imported (e.g. wheel unavailable after a Python upgrade), degrade gracefully:

```python
try:
    import faiss
except Exception:
    faiss = None

def _build_index(self, embeddings):
    if faiss is not None:
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings.astype('float32'))
    else:
        self.embeddings = embeddings.astype('float32')  # NumPy fallback

def _search(self, q_emb, k):
    if faiss is not None:
        return self.index.search(q_emb.astype('float32'), k)
    dists = ((self.embeddings - q_emb) ** 2).sum(axis=1)
    idx = dists.argsort()[:k]
    return None, idx
```

## Bootstrap gotcha

Run pip installs inside a project venv (`python3 -m venv .venv`) — the system Python is PEP 668 externally-managed and will refuse bare `pip install`.
