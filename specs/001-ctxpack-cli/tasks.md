# Tasks: ctxpack — Context Packing CLI

**Feature**: `001-ctxpack-cli` | **Spec**: [spec.md](./spec.md) · [root SPEC.md](../../SPEC.md) | **Plan**: [plan.md](./plan.md)
**Tech**: Python 3.10+, standard library only, `unittest`. Single-file `ctxpack.py` at repo root.

Test-first (red) is noted where practical. `[P]` = parallelizable (different files, no incomplete deps).
Constitution gates in force throughout: determinism, stdlib-only/offline, budget-absolute, graceful degradation,
fixed token rule `math.ceil(len/4)`, understandable code.

---

## Phase 1: Setup

- [ ] T001 Create single-file skeleton `ctxpack.py` at repo root with a `main(argv)` returning an int and a `if __name__ == "__main__": sys.exit(main(sys.argv[1:]))` guard. **Acceptance**: `python ctxpack.py` runs and exits without traceback.
- [ ] T002 [P] Create `tests/` package with `tests/__init__.py` and `tests/fixtures/` directory. **Acceptance**: `python -m unittest discover -s tests` runs (0 tests) without error.
- [ ] T003 [P] Create `README.md` stub with the clone-to-run quickstart from `specs/001-ctxpack-cli/quickstart.md`. **Acceptance**: README shows the exact `python ctxpack.py --path ... --task ... --budget ...` invocation.
- [ ] T004 [P] Create optional `pyproject.toml` declaring Python ≥3.10 and a `ctxpack` console-script entry point → `ctxpack:main`. **Acceptance**: file parses as valid TOML; no third-party deps listed.

**Checkpoint**: repo scaffolding exists; test runner works.

---

## Phase 2: Foundational — thin end-to-end (BLOCKS all user stories)

*Goal: reach Checkpoint-2 "something runs end to end, however thin" — empty bundle + manifest with correct exit codes.*

- [ ] T005 Implement `count_tokens(text) -> int` as `math.ceil(len(text)/4)` in `ctxpack.py` — the ONLY token rule. **Acceptance**: `count_tokens("abcd")==1`, `count_tokens("abcde")==2`, `count_tokens("")==0`.
- [ ] T006 [red] Add `tests/test_cli.py` asserting: missing `--budget` → exit 1; non-integer/negative budget → exit 1; missing path → exit 2; valid empty dir → exit 0. **Acceptance**: tests exist and currently fail.
- [ ] T007 Implement `parse_args(argv)` with `argparse` for `--path --task --budget --out --manifest`; override argparse's default exit (2) so **argument** errors exit **1**; one-line `ctxpack: error:` messages to stderr. **Acceptance**: T006 arg-error cases pass (exit 1).
- [ ] T008 Implement `validate_path(path)` → exit 2 with one-line stderr when path is missing/not-a-directory/unreadable. **Acceptance**: T006 missing-path case passes (exit 2).
- [ ] T009 Implement thin `main()` pipeline emitting an **empty** bundle to stdout/`--out` and a manifest (`budget/used:0/included:[]/excluded:[]`) to `--manifest`, else one-line summary to stderr. **Acceptance**: `python ctxpack.py --path <emptydir> --task x --budget 100` exits 0, prints empty bundle + summary; T006 empty-dir case passes.

**Checkpoint**: end-to-end runnable on an empty folder with correct exit codes and routing.

---

## Phase 3: User Story 1 — Pack a repo for a task within a budget (Priority: P1) 🎯 MVP

**Goal**: produce a real bundle of the most task-relevant files that never exceeds the budget, with a complete manifest.
**Independent test**: `ctxpack --path <sample> --task "fix auth" --budget 8000` → markdown bundle ≤ 8000 tokens + manifest listing included (with tokens) and excluded (with reasons).

- [ ] T010 [US1] Implement `walk(root) -> list[FileRec]` in `ctxpack.py`: recursive discovery, read as UTF-8, build `FileRec` (POSIX relative `path`, `abs_path`, `content`); results sorted by POSIX `path`. **Acceptance**: on a fixture tree, returns every text file exactly once, deterministically ordered.
- [ ] T011 [US1] Implement `rank(files, task) -> list[FileRec]`: extract task keywords (lowercase, split on non-alphanumerics, drop stopwords); score `W_path·path-hits + W_body·distinct-content-keywords(saturating) + minor depth/extension signals`; order by `(-score, tokens, posix_path)`. **Acceptance**: a file whose path/content matches the task ranks above an unrelated file; identical inputs give identical order.
- [ ] T012 [US1] Implement `render_bundle(included, tree_str) -> str`: markdown with per-file path header + fenced code block + separator; newlines normalized to `\n`. **Acceptance**: bundle contains each included file's path and fenced content; byte-identical across runs.
- [ ] T013 [US1] Implement `pack(files, budget, task)`: budget scaffolding first, then greedy fill in ranked order using `count_tokens` on each rendered block; include while it fits `remaining`; final guard `count_tokens(bundle) <= budget` (trim deterministically if needed). **Acceptance**: bundle token count ≤ budget on every fixture, including boundary budgets.
- [ ] T014 [US1] Implement `build_manifest(budget, used, included, excluded)` with exact keys `budget/used/included[{path,tokens,reason}]/excluded[{path,reason}]`; deterministic ordering; JSON via `json.dumps(..., ensure_ascii=True, separators=(",", ": "))`. **Acceptance**: manifest matches schema; `used == count_tokens(bundle)`; union(included,excluded)==considered, disjoint.
- [ ] T015 [US1] Wire US1 into `main()`: walk → rank → pack → render → manifest → emit. **Acceptance**: US1 independent test passes end-to-end on the sample folder.
- [ ] T016 [P] [red] Add `tests/test_rank_budget.py`: budget never exceeded (incl. budget just below one file), ranking places task-relevant file first, manifest accounting complete. **Acceptance**: tests pass against T010–T015.

**Checkpoint**: MVP — a real, budget-safe bundle with a complete manifest. Demoable.

---

## Phase 4: User Story 2 — Survive adversarial & degenerate input (Priority: P1)

**Goal**: never crash on hostile inputs; always a coherent result or a clean error with the right exit code.
**Independent test**: feed each adversarial category → exit 0 with valid (possibly empty) bundle, or documented error code; never a raw traceback.

- [ ] T017 [US2] Harden `walk()` encoding/readability gate: catch read/decode errors and NUL-byte sniff; unreadable/binary/non-UTF-8 files get `content=None` and are recorded for exclusion with a reason; no exception escapes. **Acceptance**: binary + latin-1 fixtures are excluded with reason, process exits 0.
- [ ] T018 [US2] Implement `is_noise(rec) -> str|None`: structural signals — vendored/VCS dirs (`.git`, `node_modules`, `venv`, `dist`, `build`, `__pycache__`), lockfile/generated shape (low entropy / `*.lock` / `*-lock.*`), minified (extreme avg line length). Returns the specific reason. **Acceptance**: a lockfile fixture and a `.git/` file are excluded with the matching reason; a normal source file is not flagged.
- [ ] T019 [US2] Implement `truncate_to_fit(text, content_budget) -> (str, bool)`: head-slice to exactly fit with visible `... [truncated: N of M tokens shown]` marker; if leftover < minimum-useful threshold, signal exclusion. Integrate into `pack()` (single file > budget → head-slice or exclude with reason). **Acceptance**: a single file larger than the budget yields a truncated block within budget, or exclusion with reason; bundle ≤ budget.
- [ ] T020 [US2] Treat included content as inert: ensure file content is only ever placed inside fenced blocks and never interpreted as tool instructions (injection posture). **Acceptance**: a fixture containing "ignore previous instructions…" is bundled verbatim inside a fence and changes no tool behavior.
- [ ] T021 [US2] Add top-level error guard in `main()`: any unexpected exception → one-line `ctxpack: error: ...` to stderr, exit 1; no traceback. **Acceptance**: forced internal error prints one line, exit 1.
- [ ] T022 [P] [red] Add `tests/test_walk_noise.py`: binary/non-UTF-8 excluded; noise signals fire; injection text inert; no crash. **Acceptance**: tests pass against T017–T021.

**Checkpoint**: hostile inputs handled; combined with US1, robust and budget-safe.

---

## Phase 5: User Story 3 — Understand & defend decisions (Priority: P2)

**Goal**: manifest accounts for every considered file with legible reasons; optional structure tree when affordable.
**Independent test**: union(included,excluded) == every file walked, each with a reason.

- [ ] T023 [US3] Ensure every considered file (source, noise, binary, truncated, budget-excluded) appears exactly once in the manifest with a specific reason string. **Acceptance**: on a mixed fixture, accounting is complete and disjoint; reasons are human-readable.
- [ ] T024 [US3] Implement affordable structure tree: render a compact tree first, include only if its `count_tokens` ≤ a small fraction of budget; drop (and note) on tiny budgets; tree tokens counted toward budget. **Acceptance**: large budget includes tree within budget; budget of 1 includes no tree and still ≤ budget.
- [ ] T025 [P] [red] Add `tests/test_manifest.py`: full accounting, disjoint sets, deterministic ordering, schema keys exact. **Acceptance**: tests pass.

**Checkpoint**: decisions are auditable and defensible in the viva.

---

## Phase 6: Polish & Cross-Cutting

- [ ] T026 [P] Add `tests/test_determinism.py`: run twice on a fixture, assert bundle bytes and manifest bytes are identical (covers repeat-run category). **Acceptance**: passes; catches any accidental nondeterminism.
- [ ] T027 [P] Add `tests/test_edgecases.py`: empty/near-empty dir, budget 0 and 1, invalid args → exit 1, missing path → exit 2 (covers remaining hidden-test categories). **Acceptance**: all pass.
- [ ] T028 [P] Add a "many files" fixture generator/test (e.g. 3,000 tiny files) asserting completion without error; record timing (STRETCH: <30s). **Acceptance**: run completes; no crash.
- [ ] T029 Finalize `README.md`: clone-to-run in <5 min, exit codes, examples, test command; verified against a fresh checkout. **Acceptance**: following README from clean clone yields a successful first run.
- [ ] T030 [P] Create `PROMPTS.md` stub (5 most important prompts: what asked / what returned / what changed & why) — graded artifact. **Acceptance**: file exists with the 5-slot structure.
- [ ] T031 [P] Create `JOURNAL.md` stub answering the five brief questions (decisions & rejected; hardest bug; where Claude Code misled & how caught; what we'd do with 2 more hours; who wrote what) — graded artifact. **Acceptance**: file exists with the 5 headings.
- [ ] T032 Run full suite `python -m unittest discover -s tests -v` and confirm all categories green; confirm no third-party imports and no network calls anywhere in `ctxpack.py`. **Acceptance**: all tests pass; `grep`-level check finds only stdlib imports.

---

## Dependencies & Execution Order

- **Phase 1 (Setup)** → **Phase 2 (Foundational, thin e2e)** must complete first — both block everything.
- **US1 (Phase 3)** is the MVP and should land next.
- **US2 (Phase 4)** builds on US1's `walk`/`pack` (hardening + truncation + noise). Can start T018 in parallel with late US1.
- **US3 (Phase 5)** depends on manifest (T014) and pack (T013).
- **Phase 6 (Polish)** last; determinism/edgecase/many-files tests exercise all prior units.

**Story independence**: US1 delivers a working, budget-safe tool on its own (MVP). US2 and US3 are additive robustness/auditability layers.

## Parallel Opportunities

- Setup: T002, T003, T004 in parallel after T001.
- Test files T016, T022, T025, T026, T027 are independent files → `[P]`.
- Graded artifacts T030, T031 in parallel any time after MVP.

## Implementation Strategy (MVP-first)

1. Ship Phases 1–2 (thin e2e) → Checkpoint 2.
2. Ship Phase 3 (US1) → demoable MVP that never exceeds budget.
3. Layer Phase 4 (US2) for hidden-test robustness, then Phase 5 (US3) for auditability.
4. Phase 6 hardens determinism + edge cases and completes graded artifacts.

**Curveball readiness**: a mid-hackathon requirement maps to exactly one unit/function (walk / noise / rank /
budget / truncate / render / manifest / cli) — change it there, re-run the category test.
