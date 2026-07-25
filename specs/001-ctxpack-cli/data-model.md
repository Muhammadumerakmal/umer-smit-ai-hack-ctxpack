# Phase 1 Data Model — ctxpack

No database. In-memory structures only; all read-only from the filesystem.

## FileRec

Represents one file discovered under `--path`.

| Field | Type | Notes |
|---|---|---|
| `path` | `str` | POSIX-normalized path relative to `--path` (forward slashes) — the deterministic sort key |
| `abs_path` | `Path` | Absolute path for reading |
| `content` | `str \| None` | Decoded UTF-8 text; `None` if unreadable/binary (then excluded) |
| `tokens` | `int` | `count_tokens(rendered_block)` once selected; `count_tokens(content)` for raw estimate |
| `score` | `float` | Relevance score from `rank()` |
| `decision` | `"included" \| "excluded"` | Final disposition |
| `reason` | `str` | Human-readable reason (why included / why excluded) |
| `truncated` | `bool` | True if a head-slice was emitted |

**Validation / rules**:
- A `FileRec` with `content is None` is always excluded with a reason (binary/non-UTF-8/unreadable).
- `path` is the final tie-breaker in every ordering → guarantees a total order.

## Args

Parsed CLI arguments.

| Field | Type | Rule |
|---|---|---|
| `path` | `str` | required; validated → exit 2 if missing/not-dir/unreadable |
| `task` | `str` | required (may be empty string; empty → all files score 0, path order decides) |
| `budget` | `int` | required; non-negative integer; else exit 1 |
| `out` | `str \| None` | optional; None → stdout |
| `manifest` | `str \| None` | optional; None → one-line summary to stderr |

## Manifest (output)

Exact keys — hidden tests bind to this.

```json
{
  "budget": 8000,
  "used": 7912,
  "included": [{"path": "src/agent.py", "tokens": 812, "reason": "path+content match; full file"}],
  "excluded": [{"path": "package-lock.json", "reason": "lockfile / generated (low-signal) content"}]
}
```

**Invariants**:
- `set(included.path) ∪ set(excluded.path) == set(every considered file.path)`, disjoint.
- `used == count_tokens(rendered_bundle) <= budget`.
- `included` sorted by rendering order (rank); `excluded` sorted by POSIX path. Both deterministic.

## Bundle (output)

Single markdown string:
- Optional title line + optional structure tree (only if affordable).
- One block per included file: a path header, a fenced code block of (possibly truncated) content, a separator.
- Newlines normalized to `\n`. `count_tokens(bundle) <= budget` always.
