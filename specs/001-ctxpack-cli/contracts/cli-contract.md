# CLI Contract — ctxpack (test-binding)

This contract is what hidden tests bind to. Implement exactly.

## Invocation

```
ctxpack --path <folder> --task "<task description>" --budget <int> [--out <file>] [--manifest <file>]
```

Also runnable as `python ctxpack.py --path ... --task ... --budget ...`.

## Flags

| Flag | Required | Type | Behavior |
|---|---|---|---|
| `--path` | yes | str | Folder to pack. |
| `--task` | yes | str | Free-text task description. |
| `--budget` | yes | int | Max tokens for the ENTIRE bundle. Non-negative. |
| `--out` | no | str | Write bundle to this file; omitted → stdout. |
| `--manifest` | no | str | Write manifest JSON to this file; omitted → one-line summary to stderr. |

## Exit codes

| Code | Condition |
|---|---|
| 0 | Success (including empty folder → empty bundle). |
| 1 | Invalid arguments: missing required flag, `--budget` not an integer, negative budget, unknown flag. |
| 2 | `--path` does not exist, is not a directory, or is unreadable. |

## Error output

- All errors: exactly one line to **stderr**, prefixed `ctxpack: error:`. No tracebacks.
- Example: `ctxpack: error: --budget must be a non-negative integer`

## stdout / stderr routing

| `--out` | `--manifest` | stdout | stderr |
|---|---|---|---|
| omitted | omitted | bundle | one-line summary |
| set | omitted | (nothing) | one-line summary |
| omitted | set | bundle | (nothing on success) |
| set | set | (nothing) | (nothing on success) |

One-line summary example (stderr): `ctxpack: 7912/8000 tokens, 12 included, 34 excluded`

## Token rule (fixed)

```python
tokens = math.ceil(len(text) / 4)
```
Applied to the complete rendered bundle, including headers/paths/fences/tree.

## Manifest JSON schema (exact keys)

```json
{
  "budget": 8000,
  "used": 7912,
  "included": [{"path": "src/agent.py", "tokens": 812, "reason": "..."}],
  "excluded": [{"path": "package-lock.json", "reason": "..."}]
}
```

## Guarantees

- `used == count_tokens(bundle) <= budget` — never exceeded.
- Byte-identical output for identical inputs (bundle and manifest).
- Every considered file appears exactly once across `included` ∪ `excluded`.
- No network calls; stdlib only; no crash on binary/non-UTF-8/unreadable/empty/huge inputs.
