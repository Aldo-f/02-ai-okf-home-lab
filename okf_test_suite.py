#!/usr/bin/env python3
"""
Test suite that runs the four verification steps you requested:
1. Front‑matter validation (simple yaml load + required keys).
2. Live‑site HTTP 200.
3. Jellyfin health‑check script + attester.
4. RAG query returns expected command with citation.
"""
import subprocess, sys, json, pathlib, yaml, os

BUNDLE_ROOT = pathlib.Path('/home/aldo/dev/02-ai-okf-home-lab')
SITE_URL = 'https://aldo-f.github.io/home-lab-docs/'

def ok(message):
    print(f"✅ {message}")

def err(message):
    print(f"❌ {message}")
    sys.exit(1)

# 1️⃣ Front‑matter validation
required = {'type','title','description','resource','tags','sources','generated','verified','status','stale_after'}
print('Running front‑matter validation...')

def parse_frontmatter(md):
    """Extract and parse only the YAML front-matter block of a markdown file."""
    text = md.read_text()
    if not text.startswith('---'):
        raise ValueError('no front-matter block')
    parts = text.split('---', 2)
    if len(parts) < 3:
        raise ValueError('malformed front-matter delimiters')
    return yaml.safe_load(parts[1]) or {}

for md in BUNDLE_ROOT.rglob('*.md'):
    rel = str(md.relative_to(BUNDLE_ROOT))
    # Only concept folders follow OKF front-matter rules; everything else
    # (RAG docs, plans, agent instructions, spec-kit files) is skipped.
    top = rel.split('/')[0]
    if not (top.startswith(('01-', '05-', '06-')) or rel in ('index.md', 'log.md')):
        continue
    try:
        data = parse_frontmatter(md)
        missing = required - data.keys()
        if missing:
            err(f"Missing keys {missing} in {md}")
    except Exception as e:
        err(f"YAML error in {md}: {e}")
ok('All markdown files have required front‑matter')

# 2️⃣ Live site HTTP 200
print('Checking live site...')
rc = subprocess.run(['curl','-fsS','-o','/dev/null','-w','%{http_code}',SITE_URL],capture_output=True,text=True).stdout.strip()
if rc!='200':
    err(f"Site returned HTTP {rc}")
ok('Live site returned 200')

# 3️⃣ Jellyfin health‑check
print('Running Jellyfin health‑check script...')
script = BUNDLE_ROOT/'05-media-jellyfin/references/skills/run-jellyfin-check.sh'
res = subprocess.run([str(script),'http://127.0.0.1:8096/health'],capture_output=True,text=True)
if res.returncode!=0 or 'Healthy' not in res.stdout:
    err('Jellyfin health‑check failed')
ok('Jellyfin health‑check script returned Healthy')

# Attester
print('Running Jellyfin attester...')
attester = BUNDLE_ROOT/'05-media-jellyfin/references/attesters/check-http.py'
res = subprocess.run(['python3',str(attester)],capture_output=True,text=True)
if res.returncode!=0 or 'OK' not in res.stdout:
    err('Jellyfin attester failed')
ok('Jellyfin attester returned OK')

# 4️⃣ RAG query
print('Testing RAG query via Hermes skill...')
# Ensure skill is registered (we'll just call the wrapper directly)
wrapper = BUNDLE_ROOT/'rag/okf_rag_serve.py'
payload = json.dumps({"question":"What is the Jellyfin health-check command?", "k":1})
res = subprocess.run(['python3',str(wrapper)],input=payload,capture_output=True,text=True)
if res.returncode!=0:
    err('RAG wrapper crashed')
out = json.loads(res.stdout)
if 'curl -fsS -m 5 http://127.0.0.1:8096/health' not in out.get('answer',''):
    err('RAG answer does not contain expected command')
if not out.get('sources'):
    err('RAG returned no sources')
ok('RAG query succeeded with proper answer and citation')

print('All tests passed!')
