---
id: 0006
title: ctxpack Spec Clarifications
stage: spec
date: 2026-07-25
surface: agent
model: claude-opus-4-8
feature: 001-ctxpack-cli
branch: main
user: muhammadumerakmal
command: /sp.clarify
labels: [clarify, ctxpack, determinism, spec-alignment]
links:
  spec: specs/001-ctxpack-cli/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/001-ctxpack-cli/spec.md
 - history/prompts/001-ctxpack-cli/0006-ctxpack-spec-clarifications.spec.prompt.md
tests:
 - none
---

## Prompt

Clarify the ctxpack spec (specs/001-ctxpack-cli/spec.md and root SPEC.md). Implementation is already complete and passing; this is a retrospective de-risking pass. Identify any genuinely underspecified or ambiguous areas that could change behavior against the hidden test set (e.g., exact tie-break ordering, tree-inclusion threshold, minimum-useful-slice threshold, how empty task text is handled, whether vendored-dir files are listed vs pruned). Only ask questions where a real ambiguity with test-impacting consequences exists; if the spec is already unambiguous, say so rather than inventing questions. Encode any answers back into the spec.

## Response snapshot

No open ambiguities required an author decision — every candidate point was already an implemented,
test-passing decision in ctxpack.py. Rather than invent questions, added a `## Clarifications` section
(Session 2026-07-25) to specs/001-ctxpack-cli/spec.md recording the exact implemented values so spec and code
cannot drift:

- Tie-break order: (-score, content_tokens asc, posix_path asc) — total order for determinism.
- Tree affordability: include only if cost <= 15% of budget (TREE_BUDGET_FRACTION=0.15) and it still fits.
- Minimum useful slice: 40 chars (MIN_SLICE_CHARS=40); below → exclude "insufficient remaining budget".
- Empty/all-stopword task: keyword signals = 0, deterministic fallback to depth → source-ext → cheaper → path.
- Vendored/VCS files: LISTED in manifest excluded (not pruned); content not read but always accounted.
- Budget invariant: enforced in characters (char_budget = budget*4) — exact, no rounding drift.

Corrected the earlier loose assumption that empty task yields pure path order (it also uses depth/ext signals).

## Outcome

- ✅ Impact: Spec now matches implementation exactly; every hidden-test category has an unambiguous spec basis.
- 🧪 Tests: none (documentation alignment); behavior already covered by the 27-test suite.
- 📁 Files: specs/001-ctxpack-cli/spec.md (Clarifications section added), this PHR.
- 🔁 Next prompts: /sp.checklist then /sp.analyze.
- 🧠 Reflection: With code already passing, clarify's value was alignment/anti-drift, not elicitation — no questions asked.

## Evaluation notes (flywheel)

- Failure modes observed: none.
- Graders run and results (PASS/FAIL): N/A.
- Prompt variant (if applicable): N/A.
- Next experiment (smallest change to try): run /sp.analyze to confirm spec/plan/tasks/code consistency.
