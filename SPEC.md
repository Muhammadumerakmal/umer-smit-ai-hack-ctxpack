# SPEC.md — `ctxpack`

**A Python standard-library CLI that packs the most task-relevant files from a folder into a
token-budgeted markdown bundle, plus an honest manifest of what it included, excluded, and why.**

Status: **written before implementation** (this is commit #1, spec only). Updated as the design
evolves; history is intentional.

---

## 1. Problem & Definition of Done

Every AI coding assistant is bottlenecked by the context window. `ctxpack` replaces a developer's
guess with a deterministic tool: given a folder, a task, and a token budget, it produces the single
best context bundle that fits the budget and an account of what it left out.

**Done means all of the following hold:**

- [ ] The exact CLI contract in §2 is implemented; hidden tests bind to it.
- [ ] The rendered bundle never exceeds `--budget` — measured on the *complete* output, not just file
      contents — verified across tiny budgets and oversized files.
- [ ] Output is deterministic: the same command twice yields byte-identical bundle **and** manifest.
- [ ] Every considered file appears exactly once in the manifest (`included` or `excluded`) with a reason.
- [ ] No adversarial input (binary, non-UTF-8, empty, huge count, injection text) produces a crash or a
      raw traceback; errors are one line with the correct exit code.
- [ ] Python 3.10+, standard library only, zero network calls at runtime.
- [ ] A judge goes from clone to first run in under 5 minutes via the README.

---

## 2. CLI Contract & Exit Codes

```
ctxpack --path <folder> --task "<task description>" --budget <int> [--out <file>] [--manifest <file>]
```

| Flag | Required | Behavior |
|---|---|---|
| `--path` | yes | Folder to pack. |
| `--task` | yes | Free-text description of what the developer is trying to do. |
| `--budget` | yes | Maximum tokens for the **entire** bundle (non-negative integer). |
| `--out` | no | Write bundle here. If omitted → stdout. |
| `--manifest` | no | Write manifest JSON here. If omitted → one-line summary to stderr. |

**Exit codes:**

| Code | Meaning | Examples |
|---|---|---|
| `0` | Success | Bundle produced (possibly empty for an empty folder). |
| `1` | Invalid arguments | Missing required flag; `--budget` not an integer; negative budget. |
| `2` | Path not found / unreadable | `--path` does not exist, is not a directory, or cannot be read. |

All errors print a single readable line to **stderr** (e.g. `ctxpack: error: --budget must be a non-negative integer`).
No raw tracebacks ever reach the user.

## 3. Token Counting (fixed, non-negotiable)

```python
tokens = math.ceil(len(text) / 4)
```

No `tiktoken`, no API. The same rule counts **everything** rendered into the bundle: headers, file-path
labels, code-fence markers, separators, and any structure tree. The budget ceiling in §5 is enforced
against the fully-rendered string, so the tool measures exactly what it emits.

## 4. Ranking Strategy — decision and rejected alternatives

**Chosen: task-keyword relevance scoring — a weighted sum of (a) path/filename keyword hits and
(b) content keyword overlap — with deterministic tie-breaking.**

Concretely, for each considered file we compute a score:

```
score = W_path * (task-keyword hits in the relative path)
      + W_body * (distinct task keywords present in file content, saturating)
      + small deterministic signals (shallower directory depth, source-code extension)
```

Task keywords are extracted from `--task` by lowercasing, splitting on non-alphanumerics, and dropping
a small stop-word set. Ranking sorts by `score` descending, then by ascending token cost (cheaper files
win ties so the budget buys more), then by POSIX relative path ascending (final, absolute tie-break → determinism).

**Why this over the alternatives:**

| Alternative | Why rejected (for a 2-hour, stdlib-only, deterministic tool) |
|---|---|
| **Filename/path match only** | Cheap and fast but blind — a file named `utils.py` may be exactly what the task needs and score zero. We keep path matching as a *strong signal* (high weight), not the only one. |
| **Content keyword overlap only** | Better recall but favors large files that mention many words by chance; also costs a full read of every file up front. We include it but saturate it so a giant file can't dominate on volume. |
| **Import-graph / dependency analysis** | Highest fidelity in theory, but language-specific, brittle on partial repos, expensive to build, and hard to make deterministic and defensible in the viva within the time box. Rejected as over-engineering for the budget of effort. |
| **File recency (mtime)** | Not portable or reproducible — mtimes differ across clones and break byte-identical repeat runs. Directly violates determinism. Rejected. |
| **Directory depth alone** | A weak heuristic (top-level files aren't always most relevant). Kept only as a minor deterministic tie-signal, never a primary ranker. |

The combination is **explainable in one sentence** ("path hits + content overlap, cheaper-wins ties,
path-sorted for determinism"), needs only the stdlib, and is fully reproducible.

## 5. Budget Enforcement — the ceiling is absolute

Greedy fill in ranked order. Maintain `remaining = budget`. For each file in ranked order, render its
block, measure the block's token cost (including its header/fences/separators), and:

- If the block fits in `remaining` → include it, subtract its cost, record it in `included`.
- If it does not fit → apply the truncation policy (§6).

Any fixed scaffolding the bundle always emits (a title line, and the optional tree in §8) is budgeted
**first** so the ceiling accounts for it. The final rendered string is asserted to be `≤ budget`; if an
off-by-one is ever possible, the tool trims deterministically rather than emit one token over.

## 6. Truncation Policy — what happens when a file doesn't fit

**Chosen: head-slice with an explicit truncation marker, gated by a minimum-useful-slice threshold.**

When a file's full block does not fit the remaining budget:

1. Compute how many tokens are left for *content* after the file's fixed block overhead (header + fences).
2. If that leftover is at least a **minimum useful threshold** (so we don't emit a 3-token stub), include a
   **head slice** of the content sized to exactly fit, append a visible marker
   (e.g. `... [truncated: N of M tokens shown]`), and record the file in `included` with a reason noting truncation.
3. If the leftover is below the threshold, **exclude** the file with a reason (`"insufficient remaining budget"`)
   and continue to the next ranked file (a later, smaller file may still fit).

**Why head-slice over the alternatives:** a "smart slice" (e.g. signatures/most-relevant-lines) is
attractive but adds language-specific parsing, more code to defend, and more determinism surface for a
marginal gain; "exclude entirely" wastes budget when a file's top is often its most informative part
(imports, class/function definitions, module docstring). Head-slice is the best budget-utilization-vs-
simplicity trade, and the marker keeps the manifest honest.

## 7. Noise Detection — without hardcoding a name list

**Chosen: signal-based detection, not a name allowlist.** A file is flagged as noise when it trips one or
more *structural* signals, and the manifest names the signal that fired:

- **Binary / non-text**: NUL byte present in a sampled prefix, or UTF-8 decode fails → `"binary or non-UTF-8"`.
- **Vendored / VCS / dependency directories**: path contains a directory that is a well-known dependency or
  VCS sink (`.git`, `node_modules`, `venv`, `dist`, `build`, `__pycache__`, …) → `"vendored/generated directory"`.
- **Lockfiles & generated manifests**: detected by *shape*, not exact name — very low token entropy / highly
  repetitive line structure, or a `*.lock` / `*-lock.*` pattern → `"lockfile / generated (low-signal) content"`.
- **Minified / single-huge-line assets**: extreme average line length → `"minified/generated asset"`.

The small directory set above is a *convenience prior*, not the mechanism: the real gate is the structural
signal (decode failure, entropy/line-shape), which catches generated files the name list has never seen.
Every noise exclusion is logged with the specific reason so the decision is auditable.

## 8. Budget Spending — is a structure tree worth its tokens?

**Chosen: include a compact project-structure tree only when it is affordable and proportionate.** The tree
is rendered first and its token cost is measured; it is emitted only if it costs less than a small fraction of
the total budget (so tiny budgets spend everything on source, not scaffolding). For a very small budget the tree
is dropped entirely and noted. Rationale: a tree orients the reader cheaply on large budgets, but on a 200-token
budget every token must be source — spending 300 tokens on a tree there would be indefensible.

## 9. Architecture (curveball-ready)

Separable units, each independently replaceable so a mid-hackathon requirement change lands in one place:

- **walk** — recursive discovery of considered files (readability/encoding gate lives here).
- **noise** — structural signal detection (§7).
- **rank** — task-keyword scoring + deterministic ordering (§4).
- **budget** — greedy fill + ceiling enforcement (§5).
- **truncate** — head-slice policy (§6).
- **render** — markdown bundle + optional tree (§8).
- **manifest** — accounting record (§10).
- **cli** — arg parsing, exit codes, stdout/stderr routing (§2).

A new requirement (e.g. "add a new ranking signal", "change bundle format") maps to exactly one unit.

## 10. Manifest Schema (exact keys)

```json
{
  "budget": 8000,
  "used": 7912,
  "included": [{"path": "src/agent.py", "tokens": 812, "reason": "path+content match; full file"}],
  "excluded": [{"path": "package-lock.json", "reason": "lockfile / generated (low-signal) content"}]
}
```

`used` is the exact token count of the rendered bundle. The union of `included` + `excluded` paths equals
every file walked. All lists are sorted deterministically.

## 11. Determinism Rules

- No timestamps, randomness, or PRNG anywhere in output.
- No dependence on `os.walk` order: results are re-sorted by explicit keys before ranking and before rendering.
- Ranking ties broken by (token cost asc, POSIX relative path asc) — total order, no ambiguity.
- JSON manifest emitted with sorted, fixed key order and stable list ordering.

## 12. Security / Injection Posture

Files may contain text engineered to manipulate an AI that reads the bundle. `ctxpack` treats **all file
content as inert data**: content is placed inside fenced blocks and never interpreted as instructions to the
tool. The tool makes no network calls and executes no file content.

## 13. Test Categories We Build For

Empty / near-empty inputs · single file larger than budget · extremely small budgets · binary / non-UTF-8
files · very large file counts · AI-manipulation text in files · invalid arguments & missing paths ·
repeat-run byte-identical output.
