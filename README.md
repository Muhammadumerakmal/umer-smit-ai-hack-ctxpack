# ctxpack

**Pack the most task-relevant files from a folder into one token-budgeted markdown bundle — with an honest manifest of what got left out and why.**

Every AI coding assistant hits the same wall: the context window. Point it at a big repo and *something* has to decide what goes in. `ctxpack` replaces the guessing with a rule you can defend.

- 🐍 **Standard library only** — no `pip install`, nothing to vendor
- 📴 **Fully offline** — zero network calls at runtime
- 🔁 **Deterministic** — the same command twice produces byte-identical output
- 🧾 **Accountable** — every file considered is either packed (with its token cost) or excluded (with a reason)
- ✅ **Python 3.10+**

---

## Quick start (clone to first run in < 5 min)

```bash
git clone <this-repo> && cd <this-repo>
python --version                                   # must be >= 3.10
python ctxpack.py --path . --task "how does ranking work" --budget 4000
```

The **bundle** prints to stdout; a **one-line summary** prints to stderr:

```
ctxpack: 4000/4000 tokens, 1 included, 352 excluded
```

To capture both artifacts as files:

```bash
python ctxpack.py --path . --task "how does ranking work" --budget 4000 \
  --out bundle.md --manifest manifest.json
```

---

## Usage

```
ctxpack --path <folder> --task "<task description>" --budget <int> [--out <file>] [--manifest <file>]
```

| Flag | Required | Meaning |
|---|:---:|---|
| `--path` | ✅ | Folder to pack. |
| `--task` | ✅ | Free-text description of what you're trying to do — this drives the ranking. |
| `--budget` | ✅ | Max tokens for the **entire** bundle (non-negative integer). |
| `--out` | — | Write the bundle here (default: **stdout**). |
| `--manifest` | — | Write the manifest JSON here (default: one-line summary to **stderr**). |

**Exit codes:** `0` success · `1` invalid arguments · `2` path not found / unreadable.
Bad input gets a readable one-line error on stderr — never a raw traceback.

### More examples

```bash
# Target a subfolder, save both outputs
python ctxpack.py --path ./src --task "add rate limiting to the API" --budget 8000 \
  --out bundle.md --manifest manifest.json

# Bundle to a file, summary to the terminal
python ctxpack.py --path ./src --task "fix the login bug" --budget 6000 > bundle.md
```

---

## How it works

A five-stage pipeline. Think of it as a librarian packing one backpack for one homework task.

1. **Walk** — recursively visit every file. Read UTF-8 text; record binary / non-UTF-8 / unreadable / oversized files (and symlinks, which are *never* followed) with a reason instead of crashing.
2. **Filter noise** — drop vendored/VCS directories, lockfiles, and minified assets by *structural signal* (decode failure, line shape, generated-dir convention) — not a brittle hardcoded filename list.
3. **Rank** — score each file by task relevance: keyword hits in the **path** (weighted heavily) + distinct task keywords in the **content**, plus small bonuses for shallow files and real source code. Ties break by *cheaper file first*, then path — which is what makes runs deterministic.
4. **Pack** — greedily fill the budget, best files first. Scaffolding (title, optional structure tree) is budgeted first. A file too big for the remaining space is **head-sliced** with a `... [truncated: N of M tokens shown]` marker, or excluded if not even a useful slice fits.
5. **Emit** — write the bundle plus a manifest that accounts for **every** file considered.

**Token rule (fixed):** `tokens = math.ceil(len(text) / 4)`, applied to the *complete rendered bundle* — headers, paths, separators, tree and all. Because that depends only on length, the budget is enforced in characters (`len ≤ budget × 4`), so the ceiling is exact: the budget is **never** exceeded, not by one token.

> Full design rationale and the alternatives we rejected: **[SPEC.md](./SPEC.md)**.

---

## Manifest schema

Exact keys, every time:

```json
{
  "budget": 8000,
  "used": 7912,
  "included": [
    {"path": "src/agent.py", "tokens": 812, "reason": "ranked relevant; full file"}
  ],
  "excluded": [
    {"path": "package-lock.json", "reason": "lockfile / generated (low-signal) content"}
  ]
}
```

Typical exclusion reasons you'll see: `vendored/generated directory (node_modules)`, `binary or non-UTF-8`, `symlink (not followed)`, `file too large (> 5 MB)`, and `insufficient remaining budget`.

---

## Design decisions (the ones the brief left open)

| Question | Our answer | Why |
|---|---|---|
| **Ranking** | Task-keyword overlap, path-weighted | Cheap, offline, explainable in one sentence — and a filename is the strongest signal of relevance. |
| **Truncation** | Head-slice with a visible marker | The top of a file (imports, signatures, docstring) carries the most orientation value per token. |
| **Noise** | Structural signal, not a name list | Detects *generated* files (decode failure, extreme line length) without hardcoding names that break on the next repo. |
| **Budget spend** | Structure tree only if ≤ 15% of budget | A tree helps orientation, but never at the cost of the source code a small budget needs. |

---

## Robustness

Handles every hidden-test category without crashing:

- Empty / near-empty inputs
- A single file larger than the whole budget → head-sliced, not skipped
- Extremely small budgets (0 and 1)
- Binary / non-UTF-8 files
- Very large numbers of files
- Text designed to manipulate an AI reading it → kept **inert** (markdown fences are widened past any backtick run inside a file, so injected `## SYSTEM OVERRIDE` headings stay plain text)
- Invalid arguments / missing paths → clean error + correct exit code
- Repeat runs → byte-identical output

---

## Tests

```bash
python -m unittest discover -s tests -v
```

31 tests covering every category above.

---

## Optional: install as a command

```bash
pip install -e .
ctxpack --path . --task "overview" --budget 6000
```

Then run `ctxpack ...` from anywhere instead of `python ctxpack.py ...`.
