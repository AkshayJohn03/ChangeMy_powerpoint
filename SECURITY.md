# Security Policy — BrandMorph

## Threat model

BrandMorph processes **untrusted PowerPoint files**. A `.pptx` is a ZIP of XML
parts, which makes it a viable attack vector in three families:

| Threat | Vector | Defense (enforced in `brandmorph/engine/safety.py`) |
|---|---|---|
| **Zip bomb** | 40 KB deck declaring petabytes of XML → disk/memory exhaustion | Declared-size cap (250 MB default, env-tunable) + per-entry compression-ratio cap (×200) + entry-count cap, checked against the central directory before any parse |
| **Zip slip** | Archive entry paths like `../../evil.xml` | Every entry path validated (no absolute, no `..`, no backslashes) |
| **XML entity bomb** ("billion laughs") | DTD entity expansion inside theme/slide XML | All engine XML parsing uses a hardened lxml parser: `resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False` |

Additional API surface defenses:

- **Upload cap** — request bodies stream to disk with a hard size limit
  (`BRANDMORPH_MAX_UPLOAD`, default 120 MB); oversized uploads are truncated
  and rejected without loading into memory.
- **Unsafe-deck semantics** — a hostile deck returns HTTP 422 with the exact
  rule it tripped; batch endpoints isolate decks so one malicious file cannot
  poison the batch.
- **CORS** — explicit env-configurable allowlist (v1 shipped wildcard +
  credentials); never enable `*` together with credentials.
- **Secrets** — no API keys in code; the optional LLM copy-rewriting path
  reads `LLM_API_KEY` from the environment only.

## Known limitations (honest)

- python-pptx internally parses XML with its own lxml parser; our hardened
  parser covers the parts *we* parse (theme/slide trees we touch) and the
  pre-validation caps bound what python-pptx will ever see. A fully hardened
  deployment should still run the service in a container with resource limits.
- No authentication is enforced by default for local/desktop use. For
  multi-tenant deployment, put the service behind an authenticating reverse
  proxy or enable one at the gateway layer (see the AegisGate pattern).

## Reporting

Open a GitHub issue marked `security` — do not include hostile files in the
report; describe the tripped rule instead.
