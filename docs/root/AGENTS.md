# AGENTS.md — 06-apps-aldo-f-github-io

## Overview
Personal documentation hub (MkDocs + Material theme) deployed to https://aldo-f.github.io via GitHub Pages.
Aggregates documentation from other repos at build time using `mkdocs-multirepo-plugin`.

## Structure
```
06-apps-aldo-f-github-io/
├── docs/                     # This site's own content (home page)
├── download/                 # Static downloads served via docs (CV, etc.)
├── .github/workflows/deploy.yml  # CI: build + deploy on push to main
├── mkdocs.yml                # Site config: theme, plugins, nav, multirepo imports
├── requirements.txt          # Python deps: mkdocs, mkdocs-material, mkdocs-multirepo-plugin
└── AGENTS.md                 # This file
```

## HOW THE MULTIREPO DOCS WORK
- `mkdocs.yml` → `plugins.multirepo.nav_repos` lists remote repos/branches.
- At `mkdocs build` time the plugin clones each repo and copies its `docs/` folder in.
- Nav entries reference imported paths, e.g. `thuis/docs/index.md`.
- To add a repo's docs: add a `nav_repos` entry (name + `import_url?branch=`) AND a matching nav item.

## WHERE TO LOOK
| File | Purpose |
|------|---------|
| `mkdocs.base.yml` | Shared config: theme, common plugins/extensions/social, hooks |
| `mkdocs.en.yml` | EN build (INHERIT base): `docs/en`, site root, multirepo imports |
| `mkdocs.nl.yml` | NL build (INHERIT base): `docs/nl`, served at `/nl/` |
| `hooks/slugmap.py` | Build hook: emits `slugmap.json` + language-switch interceptor |
| `docs/en/` | EN content (blog posts in `docs/en/blog/posts/`) |
| `docs/nl/` | NL content (Dutch home/about/blog) |
| `.github/workflows/deploy.yml` | Deployment pipeline: two strict builds (EN root, NL `/nl/`) on push to `main` |
| `requirements.txt` | Python dependencies for build |

## CONVENTIONS
- Multilingual via Material multi-build recipe: one strict build per language;
  every `mkdocs build` MUST name its config (`-f mkdocs.en.yml` / `-f mkdocs.nl.yml`)
- `INHERIT` REPLACES list values (plugins/nav/theme.features/hooks) instead of
  merging — keep each language config self-complete for those keys
- Blog posts live in `docs/<lang>/blog/posts/`; publishing = adding ONE markdown
  file with `title` + `date` front matter (`draft: true` keeps it out of production)
- Mirrored posts share the FILENAME across languages (sync key); URL slugs
  derive from the translated title, so they differ per language
- After adding/changing post categories, re-run
  `./venv/bin/python scripts/gen_category_index.py` (per-language overview tables;
  `tests/verify_blog.py` fails if stale)
- To fill translation gaps: `autotranslate --docs-dir docs --paths . --exclude 'blog/category/*'`
  (dry-run) then `--write`, review the diff, re-run the category generator, commit.
  Provided by the `mkdocs-autotranslate` plugin (PyPI); DeepL key lives outside
  the repo (`~/.config/deepl/api_key`). Plugin config lives in `mkdocs.base.yml`
- Remote repos must keep their documentation under a top-level `docs/` folder to be importable
- Versioned docs = extra `nav_repos` entry pinned to a tag/branch (see `thuis-v3.0.0` example)
- Deploy only happens on pushes to `main` (GitHub Actions, `build_type: workflow`)
- Build locally with `mkdocs serve`; output goes to `site/` (not committed)

## ANTI-PATTERNS
- ❌ Editing files in `site/` directory directly — regenerated on each build
- ❌ Committing `site/`, `venv/`, or imported repo caches to git
- ❌ Adding multirepo entries without a matching `nav:` item — they won't appear
- ❌ Renaming/moving this repo's default branch without updating `deploy.yml` trigger
- ❌ Using Jekyll/Hugo concepts here (legacy leftovers have been removed) — this is MkDocs
