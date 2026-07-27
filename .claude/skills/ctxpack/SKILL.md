---
name: ctxpack
description: Pack the most task-relevant files from a folder into a token-budgeted markdown bundle with an honest include/exclude manifest. Use when you need to hand another model (or yourself) a compact, budget-bounded context pack from a directory — e.g. "bundle this repo under N tokens for task X", "build a context pack", "which files fit in my budget". Deterministic, stdlib-only, no network.
---

# ctxpack — token-budgeted context bundler

`ctxpack.py` walks a folder, ranks files by how well they match a free-text task,
and greedily fills a **token budget** with the most relevant files — emitting a
markdown bundle plus a JSON manifest that says exactly what was included/excluded
and why. It is deterministic (same inputs → byte-identical output), uses only the
Python standard library, and makes no network calls.

The tool lives at the repo root: `ctxpack.py`. The authoritative contract is
`SPEC.md`; read it before changing behavior.

## When to use this

- You need to feed a directory's most relevant files to an LLM under a hard token cap.
- You want a defensible manifest of *why* each file was in or out.
- You want reproducible packing (CI, snapshot tests, sharing bundles).

Do **not** reach for it for fuzzy semantic search or embeddings — ranking is
keyword/path based by design (see "How ranking works").

## How to run

```bash
python ctxpack.py --path <folder> --task "<free text>" --budget <int> \
  [--out bundle.md] [--manifest manifest.json]
```

Required:
- `--path` — folder to pack (must exist, be a directory, be readable).
- `--task` — free-text task description; its keywords drive ranking.
- `--budget` — max tokens for the **entire** bundle (non-negative integer).

Optional:
- `--out` — write the bundle here (default: stdout).
- `--manifest` — write the manifest JSON here (default: a one-line summary to stderr).

### Examples

Bundle the current repo for an auth task, cap at 8k tokens, save both artifacts:

```bash
python ctxpack.py --path . --task "harden the budget invariant and exclusion logic" \
  --budget 8000 --out bundle.md --manifest manifest.json
```

Quick pack to stdout with just a stderr summary:

```bash
python ctxpack.py --path ./src --task "http retry timeout handling" --budget 4000
```

## Token rule (the one invariant)

`tokens = ceil(len(text) / 4)`. Because it depends only on length, the budget is
enforced in **characters** (`budget * 4`) so the ceiling is exact. The bundle is
**guaranteed** to satisfy `tokens(bundle) <= budget` — `pack()` raises rather than
emit an over-budget bundle. If you change scoring or rendering, preserve this.

## How ranking works

Each candidate file gets a score (higher = packed sooner):

| Signal | Weight | Meaning |
|---|---|---|
| task keyword in **path** | `W_PATH = 5.0` | per occurrence — strongest signal |
| distinct task keyword in **body** | `W_BODY = 1.0` | saturates at #keywords |
| shallower file | `W_DEPTH = 0.25` | small orientation bonus |
| source-code extension | `W_SRC_EXT = 0.5` | small bonus |

Keywords come from `--task`: lowercased, split on non-alphanumerics, stopwords and
1-char tokens dropped. Total order for packing: **score desc, then fewer tokens
(cheaper) first, then path ascending** — fully deterministic.

## What gets excluded (and is said so in the manifest)

Pre-ranking gates, each recorded with a reason:
- vendored/generated dirs (`.git`, `node_modules`, `dist`, `__pycache__`, …)
- symlinks (never followed — could point outside `--path`)
- files `> 5 MB` (memory guard)
- binary / non-UTF-8 (NUL sniff + decode check)
- lockfiles (`package-lock.json`, `*.lock`, …)
- minified/generated assets (extreme average line length)

Then budget exclusions: relevant files that didn't fit get `"insufficient
remaining budget"`. Files too big to fit whole are **head-sliced** with a visible
`... [truncated: X of Y tokens shown]` marker when a useful slice fits.

## Manifest schema

```json
{
  "budget": 8000,
  "used": 7960,
  "included": [ { "path": "...", "tokens": 123, "reason": "ranked relevant; full file" } ],
  "excluded": [ { "path": "...", "reason": "vendored/generated directory (node_modules)" } ]
}
```

`included` is in render (rank) order; `excluded` is sorted by path.

## Exit codes

- `0` — success.
- `1` — bad arguments (`--budget` not a non-negative int, missing required flag) or an internal error (one line to stderr, never a traceback).
- `2` — `--path` missing / not a directory / unreadable.

## Safety notes (why the output is trustworthy)

- Code fences are widened past any backtick run in a file, and filenames are
  sanitized, so a file containing ` ``` ` or a `## SYSTEM OVERRIDE` heading can't
  break out of its block — an injection guard.
- Output is written as raw UTF-8 bytes with normalized `\n` line endings, so
  bundles are byte-identical across OSes.

## Verifying changes

Tests live in `tests/`. After any edit to `ctxpack.py`, run them and confirm the
budget invariant still holds:

```bash
python -m pytest tests/ -q
```
