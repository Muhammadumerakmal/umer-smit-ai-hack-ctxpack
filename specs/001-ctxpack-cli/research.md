# Phase 0 Research — ctxpack

All "NEEDS CLARIFICATION" resolved. Each decision records rationale and rejected alternatives so it is
defensible in the viva.

## R1. Ranking method

- **Decision**: Weighted task-keyword score = `W_path·(keyword hits in relative path) + W_body·(distinct
  task keywords found in content, saturating) + minor deterministic signals (shallow depth, source extension)`.
  Order by `(-score, tokens_asc, posix_path_asc)`.
- **Rationale**: Uses only stdlib string ops; explainable in one sentence; fully reproducible; cheaper-file
  tie-break maximizes files-per-budget.
- **Alternatives considered**: import-graph (language-specific, brittle, hard to make deterministic — rejected);
  file recency/mtime (non-reproducible across clones, breaks determinism — rejected); path-only (blind to
  content — kept only as a strong signal); content-only (favors large files, full read up front — saturated, not sole).

## R2. Truncation policy

- **Decision**: Head-slice sized to exactly fit remaining content budget, with a visible
  `... [truncated: N of M tokens shown]` marker, gated by a minimum-useful-slice threshold; below threshold → exclude with reason.
- **Rationale**: File tops (imports, defs, docstring) are usually most informative; marker keeps manifest honest;
  no language parsing needed.
- **Alternatives**: smart/semantic slice (needs per-language parsing, more determinism surface — rejected for time box);
  blind exclude (wastes budget — rejected).

## R3. Noise detection without a hardcoded name list

- **Decision**: Structural signals — (a) NUL byte in sampled prefix or UTF-8 decode failure → binary;
  (b) path traverses a known dependency/VCS sink directory (`.git`, `node_modules`, `venv`, `dist`, `build`,
  `__pycache__`) as a convenience prior; (c) lockfile/generated shape via low entropy / highly repetitive lines
  or `*.lock`/`*-lock.*`; (d) minified assets via extreme average line length.
- **Rationale**: The real gate is the structural signal, which catches unseen generated files; the directory set
  is a prior, not the mechanism. Every exclusion logs the specific signal.
- **Alternatives**: pure hardcoded filename list (brittle, misses novel generated files — rejected as sole method);
  gitignore-only (stretch; not every noise file is git-ignored — deferred to STRETCH).

## R4. Budget spending on a structure tree

- **Decision**: Render a compact tree first; include only if its token cost ≤ a small fraction of total budget;
  drop entirely on tiny budgets and note it.
- **Rationale**: Orientation is cheap and useful on large budgets; on a 200-token budget every token must be source.
- **Alternatives**: always include tree (indefensible on tiny budgets — rejected); never include (loses cheap
  orientation on large budgets — rejected).

## R5. Token counting

- **Decision**: `math.ceil(len(text)/4)` in a single `count_tokens()` used for every measurement, including scaffolding.
- **Rationale**: Fixed by the brief for cross-team comparability; one function guarantees the absolute-budget
  invariant is measured consistently.
- **Alternatives**: tiktoken / model tokenizers (forbidden — rejected).

## R6. Argument parsing & exit codes

- **Decision**: `argparse` with custom error handling so invalid args exit `1` (not argparse's default `2`); path
  errors exit `2`; success `0`. All errors one line to stderr, prefixed `ctxpack: error:`.
- **Rationale**: Exit-code contract is bound by hidden tests; argparse default exit code (2) must be overridden to
  match the brief's mapping.
- **Alternatives**: hand-rolled parser (more code to own — rejected); leave argparse default codes (violates
  contract: argparse uses 2 for arg errors, brief wants 1 — rejected).

## R7. Determinism mechanics

- **Decision**: Explicit total-order sort keys everywhere; normalize newlines to `\n`; JSON with fixed key order
  and no set iteration; no time/random/mtime.
- **Rationale**: Byte-identical repeat runs are directly tested.
- **Alternatives**: rely on filesystem/dict order (nondeterministic across OS/runs — rejected).

## R8. Test framework

- **Decision**: stdlib `unittest`, run via `python -m unittest`.
- **Rationale**: Honors stdlib-only; no pip install for judges.
- **Alternatives**: pytest (third-party — rejected for parity with the stdlib-only constraint).

## Potential ADR

R1 (ranking), R2 (truncation), R3 (noise detection) are architecturally significant (long-term impact,
multiple viable alternatives, cross-cutting). Candidate for a single grouped ADR: "Selection heuristics for
ctxpack (ranking, truncation, noise)."
