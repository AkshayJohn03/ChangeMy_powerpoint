# Data-compliance policy (binding)

1. **Never display real deck filenames, file paths, slide text, client names,
   or any deck contents** in chat output, tool arguments, or logs.
2. All decks in `data/source/**` are physically renamed to opaque ids
   (`deck_0001.pptx`, …). Always refer to decks by these opaque ids.
3. The ONLY mapping from opaque id to original identity is
   `data/metadata/deck_registry.json` — RESTRICTED: never print, cat, grep,
   or transmit this file. It is gitignored.
4. Python pipelines may read full contents locally for feature extraction and
   training. The assistant may only see **aggregate statistics** (counts,
   distributions, metrics) or **synthetic verification decks** built in tests.
5. No deck content may be sent to any cloud service / external API.
6. Before committing anything under `data/` (whitelisted aggregates only),
   run the leakage self-check:

```bat
.\backend\venv\Scripts\python.exe -m morphlite.tests.test_no_leakage
```

It must PASS. In practice: `data/` is fully gitignored and never committed.

## Git rules derived from this policy

- `data/`, `session-ses_*.md`, `*.joblib`, `__pycache__/`, `*.pyc` — ignored.
- Deck-bearing binaries (`*.pptx`), logs (`*.log`), local builds (`build/`,
  `dist/`), installers (`*.exe`), venvs, `node_modules/`, `.env` — ignored.
- Commit only source, docs, configs and tiny aggregate metadata.
