# PROMPTS.md — the 5 most important prompts

For each: what we asked, what Claude Code returned, and what we changed and why.
*(Seeded from the build session — the team should trim/expand to the 5 that mattered most and add the exact
wording you used.)*

---

## Prompt 1 — Constitution from the brief

**Asked**: Turn the hackathon brief into a project constitution with non-negotiable principles (spec-first,
determinism, stdlib-only, graceful degradation, absolute budget, defensible decisions, ownership, fixed token rule).

**Got back**: `.specify/memory/constitution.md` v1.0.0 with 8 principles mapped 1:1 to the grading axes, plus a
technical-constraints section (CLI contract, exit codes, manifest schema).

**Changed & why**: Kept it; it became the checklist we validated every later step against (the "budget is
absolute" and "determinism" gates in particular).

---

## Prompt 2 — SPEC.md before any code

**Asked**: Write `SPEC.md` documenting the CLI contract, ranking strategy *with rejected alternatives*,
truncation policy, noise detection without a hardcoded name list, budget-spending decision, and definition of done.

**Got back**: A structured SPEC with a decision table (why not import-graph, why not recency, etc.).

**Changed & why**: We committed this **first, with no code**, to satisfy the spec-quality gate. We tightened the
budget section to state the char-equivalence trick (`len ≤ budget×4`) once we discovered it during planning.

---

## Prompt 3 — Modular plan that can absorb the curveball

**Asked**: Produce an implementation plan with 8 separable units (walk/noise/rank/budget/truncate/render/
manifest/cli) so a mid-hackathon requirement lands in exactly one place.

**Got back**: `plan.md` with function signatures, a determinism strategy, and a budget-accounting order.

**Changed & why**: Adopted the single-file design (`ctxpack.py`) with pure functions — easiest to audit under
stdlib-only and to explain in the viva.

---

## Prompt 4 — Implement with the budget enforced in characters

**Asked**: Build `ctxpack.py` + stdlib `unittest` suite; enforce `tokens = ceil(len/4)` via one function and
guarantee the budget is never exceeded.

**Got back**: Working implementation; the key move was enforcing the budget in **characters** (`len ≤ budget×4`)
so the ceiling is exact and additive — no per-block rounding drift.

**Changed & why**: This replaced a naive "sum of per-file token counts" approach that could drift by a token per
file. The char-budget makes the "never exceed by one token" guarantee provable.

---

## Prompt 5 — Test per hidden-test category

**Asked**: Write one test per hidden-test category (empty, single-file-over-budget, tiny budgets, binary/non-UTF8,
many files, injection-inert, invalid args, repeat-run byte-identical).

**Got back**: 27 tests across 6 files; all green.

**Changed & why**: Added a byte-identical determinism test that runs the CLI twice and diffs the bytes — it is the
single most valuable regression guard for the "repeat runs" category.

---

> Question-3 material for the journal: note any point where Claude Code confidently produced something wrong and
> how you caught it (see `JOURNAL.md`).
