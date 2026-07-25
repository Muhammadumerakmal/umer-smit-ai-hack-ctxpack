# Implementation Plan: ctxpack — Context Packing CLI

**Branch**: `001-ctxpack-cli` | **Date**: 2026-07-25 | **Spec**: [spec.md](./spec.md) · [root SPEC.md](../../SPEC.md)
**Input**: Feature specification from `specs/001-ctxpack-cli/spec.md`

## Summary

`ctxpack` walks a folder, ranks readable text files by relevance to a free-text task, and greedily packs
the highest-ranked files into a single markdown bundle that never exceeds a token budget
(`math.ceil(len(text)/4)`), emitting a manifest that accounts for every file considered. Technical
approach: a single-file `ctxpack.py` composed of eight internally-separable pure functions
(walk → noise → rank → budget/truncate → render → manifest) behind an argparse CLI, with determinism
enforced by explicit total-order sort keys and zero use of time/randomness/mtime.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: Standard library only (`argparse`, `os`/`pathlib`, `json`, `math`, `sys`, `re`). No third party.
**Storage**: Filesystem read-only input; output to stdout or `--out` file, manifest to stderr or `--manifest` file.
**Testing**: `unittest` (stdlib) — no pytest dependency, to honor stdlib-only. Runnable via `python -m unittest`.
**Target Platform**: Any OS with Python 3.10+ (Windows/macOS/Linux); must run offline on a clean machine.
**Project Type**: Single project — one CLI entry point (`ctxpack.py`) at repo root.
**Performance Goals**: Correctness first; STRETCH 3,000 files < 30s (single pass, bounded per-file reads).
**Constraints**: No network at runtime; deterministic byte-identical output; budget never exceeded by one token; no raw tracebacks.
**Scale/Scope**: Folders from 0 to thousands of files; individual files from empty to larger-than-budget.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Plan compliance |
|---|---|---|
| I. Spec-Driven Development | Spec precedes code; spec is commit #1 | ✅ SPEC.md committed spec-only before this plan |
| II. Deterministic Output | Byte-identical repeat runs | ✅ Explicit total-order sort keys; no time/rand/mtime; JSON with fixed key order |
| III. Stdlib Only, Offline | No third party, no network | ✅ Only `argparse/os/pathlib/json/math/sys/re`; zero sockets |
| IV. Graceful Degradation | No crash on adversarial input | ✅ Per-file try/except → excluded+reason; top-level guard maps errors to exit codes |
| V. Budget Is Absolute | Complete output ≤ budget | ✅ Scaffolding budgeted first; greedy fill measures rendered blocks; final assert-and-trim |
| VI. Every Decision Defensible | Alternatives documented | ✅ SPEC §4–§8 + research.md record rejected options |
| VII. You Own Every Line | Explainable, boring code | ✅ Pure functions, small, no metaprogramming |
| VIII. Fixed Token Rule | `ceil(len/4)` everywhere | ✅ One `count_tokens()` used for all measurements |

**Result: PASS** — no violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/001-ctxpack-cli/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions & rejected alternatives
├── data-model.md        # Phase 1 — entities & structures
├── quickstart.md        # Phase 1 — clone-to-run in <5 min
├── contracts/
│   └── cli-contract.md   # Phase 1 — CLI + manifest contract (test-binding)
└── tasks.md             # Phase 2 — created by /sp.tasks (not here)
```

### Source Code (repository root)

```text
ctxpack.py               # Single-file CLI entry point (python ctxpack.py ...)
pyproject.toml           # Optional installed entry point (console_scripts: ctxpack)
README.md                # Clone-to-run in <5 min (graded)
tests/
├── test_cli.py          # arg parsing, exit codes, stdout/stderr routing
├── test_walk_noise.py   # discovery, encoding gate, structural noise signals
├── test_rank_budget.py  # ranking order, greedy fill, truncation, budget ceiling
├── test_determinism.py  # repeat-run byte-identical bundle + manifest
└── fixtures/            # tiny sample trees incl. binary, injection, oversized
```

**Structure Decision**: Single project. The brief mandates `python ctxpack.py ...` from a clean machine,
and stdlib-only keeps the whole tool comfortably in one auditable file with functions that map 1:1 to the
SPEC's eight units. `tests/` uses stdlib `unittest`. `pyproject.toml` is optional sugar for `ctxpack` as an
installed command; it is not required for judging.

## Architecture — module boundaries & signatures

All units are pure functions in `ctxpack.py` (single file, but internally separable — the curveball lands
in exactly one function). Core data object is a small dict/dataclass `FileRec`.

```python
def count_tokens(text: str) -> int                      # math.ceil(len(text)/4) — the ONLY token rule

def parse_args(argv: list[str]) -> Args                 # argparse; raises ArgError(msg) → exit 1
def validate_path(path: str) -> Path                    # missing/not-dir/unreadable → PathError(msg) → exit 2

def walk(root: Path) -> list[FileRec]                   # recursive; readability+encoding gate; sorted by POSIX path
def is_noise(rec: FileRec) -> str | None                # returns reason if noise (structural signal) else None
def rank(files: list[FileRec], task: str) -> list[FileRec]   # score desc, tokens asc, POSIX path asc

def pack(files, budget, task) -> tuple[list[FileRec], list[FileRec], str]
                                                        # greedy fill; returns (included, excluded, bundle_str)
def truncate_to_fit(text: str, content_budget: int) -> tuple[str, bool]  # head-slice + marker; min-slice gate

def render_bundle(included, tree_str) -> str            # markdown; scaffolding already budgeted
def build_manifest(budget, used, included, excluded) -> dict   # exact schema; deterministic ordering

def main(argv) -> int                                   # orchestrates; maps exceptions → exit codes 0/1/2
```

**Data flow**: `parse_args → validate_path → walk → (is_noise filter) → rank → pack(+truncate) →
render_bundle → build_manifest → emit(out/stdout, manifest/stderr) → exit code`.

## Determinism strategy

- **No** `time`, `random`, or `st_mtime` anywhere in output-affecting logic.
- `walk` re-sorts results by POSIX relative path — `os.walk` order never leaks.
- `rank` uses a **total order**: `(-score, tokens, posix_path)` — no ties can reorder nondeterministically.
- Manifest lists sorted by POSIX path; JSON emitted with fixed key insertion order and
  `json.dumps(..., ensure_ascii=True, separators=(",", ": "))` (no set iteration).
- Line endings normalized to `\n` in the bundle so output is identical across OSes.

## Token-budget accounting order

1. Compute fixed scaffolding (bundle title; optional structure tree only if it costs ≤ a small fraction of budget).
2. `remaining = budget − scaffolding_tokens`. If scaffolding alone would exceed budget, drop the tree, then
   the title, until it fits (tiny-budget path).
3. Greedy fill in ranked order: for each file, render its block, measure with `count_tokens`; include if it
   fits `remaining`, else `truncate_to_fit` (head-slice) if the leftover ≥ min-useful threshold, else exclude
   with reason and continue.
4. Final guard: `assert count_tokens(bundle) <= budget`; if equal-boundary rounding ever risks +1, trim the
   last block deterministically. `used = count_tokens(bundle)`.

## Error handling & exit-code mapping

| Situation | Handling | Exit |
|---|---|---|
| Success | Emit bundle + manifest | `0` |
| Missing/invalid flag, non-int/negative budget | `ArgError` → one-line stderr | `1` |
| `--path` missing / not a dir / unreadable | `PathError` → one-line stderr | `2` |
| Per-file read/decode failure | caught → file added to `excluded` with reason; no crash | `0` |
| Unexpected internal error | top-level `except` → one-line `ctxpack: error: ...` | `1` |

Every `print` of an error goes to **stderr** prefixed `ctxpack: error:`; no traceback escapes.

## Test plan (aligned to hidden-test categories)

| Category | Test |
|---|---|
| Empty / near-empty input | empty dir → exit 0, empty bundle, manifest used:0 |
| Single file > budget | oversized file → head-slice or exclude; bundle ≤ budget |
| Extremely small budget | budget 1 and 0 → output ≤ budget, exit 0 |
| Binary / non-UTF-8 | NUL file + latin-1 file → excluded with reason, no crash |
| Very many files | 3,000-file fixture → completes; (stretch timing) |
| Injection text in files | file with "ignore previous instructions" → content fenced, inert |
| Invalid args / missing path | missing --budget → exit 1; missing path → exit 2 |
| Repeat-run byte-identical | run twice, `assertEqual` bundle and manifest bytes |

## Complexity Tracking

No constitution violations — table intentionally omitted.

## Phase 2 handoff

`/sp.tasks` will decompose this into dependency-ordered tasks: token rule + CLI skeleton → walk/encoding gate
→ noise signals → ranking → budget/truncate → render+tree → manifest → error mapping → test suite by category
→ README/quickstart. Test-first (red) per category where practical.
