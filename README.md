# ctxpack

Pack the most **task-relevant** files from a folder into a single markdown bundle that fits a **token
budget**, plus an honest **manifest** of what was included, excluded, and why.

Standard library only. No network. Deterministic (byte-identical repeat runs). Python 3.10+.

## Clone to first run (< 5 minutes)

```bash
git clone <this-repo> && cd <this-repo>
python --version            # must be >= 3.10
python ctxpack.py --path . --task "how does ranking work" --budget 4000
```

The **bundle** goes to stdout; a one-line **summary** goes to stderr.

## Usage

```
ctxpack --path <folder> --task "<task description>" --budget <int> [--out <file>] [--manifest <file>]
```

| Flag | Required | Meaning |
|---|---|---|
| `--path` | yes | Folder to pack. |
| `--task` | yes | Free-text description of what you're trying to do. |
| `--budget` | yes | Max tokens for the **entire** bundle (non-negative integer). |
| `--out` | no | Write the bundle here (default: stdout). |
| `--manifest` | no | Write the manifest JSON here (default: one-line summary to stderr). |

**Exit codes:** `0` success · `1` invalid arguments · `2` path not found / unreadable.

### Examples

```bash
# Bundle + manifest to files
python ctxpack.py --path ./src --task "add rate limiting to the API" --budget 8000 \
  --out bundle.md --manifest manifest.json

# Just the summary (bundle to stdout, summary to stderr)
python ctxpack.py --path ./src --task "fix the login bug" --budget 6000 > bundle.md
```

## How it works (short version)

1. **Walk** the folder; read UTF-8 text. Binary / non-UTF-8 / unreadable files are skipped and recorded.
2. **Filter noise** by *structural signal* (vendored/VCS dirs, lockfile shape, minified assets) — not a
   hardcoded name list.
3. **Rank** files by task-keyword relevance: hits in the path (weighted high) + distinct task keywords in
   the content, with a small bonus for shallow, source-code files. Ties break by *cheaper file first*, then path.
4. **Pack** greedily under the budget. Scaffolding (title, optional structure tree) is budgeted first. A file
   too big for what's left is **head-sliced** with a `... [truncated: N of M tokens shown]` marker, or excluded.
5. **Emit** the bundle and a manifest that accounts for **every** file considered.

**Token rule (fixed):** `tokens = math.ceil(len(text) / 4)`, applied to the complete rendered bundle. Because
that depends only on length, the tool enforces the budget in characters (`len ≤ budget × 4`) so the ceiling is
exact — the budget is **never** exceeded, not by one token.

Full design rationale and rejected alternatives: **[SPEC.md](./SPEC.md)**.

## Manifest schema

```json
{
  "budget": 8000,
  "used": 7912,
  "included": [{"path": "src/agent.py", "tokens": 812, "reason": "ranked relevant; full file"}],
  "excluded": [{"path": "package-lock.json", "reason": "lockfile / generated (low-signal) content"}]
}
```

## Tests

```bash
python -m unittest discover -s tests -v
```

Covers every hidden-test category: empty/near-empty input, single file larger than budget, tiny budgets
(0 and 1), binary/non-UTF-8 files, many files, injection text (kept inert), invalid args / missing paths,
and byte-identical repeat runs.

## Optional: install as a command

```bash
pip install -e .
ctxpack --path . --task "overview" --budget 6000
```
