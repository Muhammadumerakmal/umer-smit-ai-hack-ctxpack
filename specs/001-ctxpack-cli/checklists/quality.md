# Checklist: ctxpack Requirements Quality

**Purpose**: Unit-tests-for-English — validate that the ctxpack requirements are complete, clear, consistent,
and measurable before trusting them as the basis for the hidden test set. Tests the *requirements*, not the code.
**Created**: 2026-07-25
**Feature**: [spec.md](../spec.md) · Root deliverable: [SPEC.md](../../../SPEC.md)

## Requirement Completeness

- [x] CHK001 - Are budget requirements stated for the **complete rendered bundle** (headers, paths, fences, tree), not only file contents? [Completeness, Spec §FR-004, SPEC §5]
- [x] CHK002 - Is a requirement present for **every** hidden-test category (empty, over-budget file, tiny budget, binary/non-UTF-8, many files, injection, invalid args, repeat-run)? [Coverage, Spec §Edge Cases]
- [x] CHK003 - Are exit-code requirements documented for all three outcomes (0/1/2) with the triggering conditions enumerated? [Completeness, Spec §FR-008, contracts/cli-contract.md]
- [x] CHK004 - Is the manifest schema specified with exact keys and per-entry fields (`included{path,tokens,reason}`, `excluded{path,reason}`)? [Completeness, Spec §FR-005]
- [x] CHK005 - Is the accounting invariant stated (union of included+excluded == every considered file, disjoint)? [Completeness, Spec §SC-004, data-model.md]
- [x] CHK006 - Are the graded deliverables enumerated as requirements (SPEC.md, README.md, CLAUDE.md, PROMPTS.md, JOURNAL.md)? [Completeness, SPEC §1]
- [x] CHK007 - Are stdout/stderr routing requirements defined for all four `--out`/`--manifest` combinations? [Completeness, contracts/cli-contract.md]

## Requirement Clarity (vague terms quantified)

- [x] CHK008 - Is the token rule stated as an exact formula rather than "approximately"? [Clarity, Spec §FR-004: `ceil(len/4)`]
- [x] CHK009 - Is "affordable structure tree" quantified rather than left as "if justified"? [Clarity, Spec §Clarifications: ≤15% of budget]
- [x] CHK010 - Is "minimum useful slice" quantified with a concrete threshold? [Clarity, Spec §Clarifications: 40 chars]
- [x] CHK011 - Is the ranking tie-break order stated as an explicit total order, not "sorted by relevance"? [Clarity, Spec §Clarifications: `(-score, tokens, path)`]
- [x] CHK012 - Is "handle without crashing" made measurable (documented exit code + one-line error, no traceback)? [Measurability, Spec §FR-008]
- [x] CHK013 - Is "noise" defined by detectable signals rather than an open-ended adjective? [Clarity, Spec §FR-010, SPEC §7]
- [x] CHK014 - Is behavior for an **empty/all-stopword** `--task` explicitly specified? [Clarity, Spec §Clarifications]

## Requirement Consistency

- [x] CHK015 - Does the token rule read identically across spec, plan, contract, and README (no drift)? [Consistency, Spec §FR-004 / SPEC §3 / cli-contract.md]
- [x] CHK016 - Do the exit-code definitions match between spec, root SPEC, and the CLI contract? [Consistency, contracts/cli-contract.md]
- [x] CHK017 - Is the determinism requirement consistent everywhere (byte-identical bundle AND manifest)? [Consistency, Spec §FR-007, §SC-002]
- [x] CHK018 - Do the Clarifications values agree with the plan's stated constants (tree fraction, min slice, tie-break)? [Consistency, plan.md ↔ spec §Clarifications]

## Acceptance Criteria Quality (measurable)

- [x] CHK019 - Is "never exceed budget" expressed as an objectively checkable criterion (100% of runs, complete output)? [Measurability, Spec §SC-001]
- [x] CHK020 - Is determinism expressed as a checkable criterion (repeat runs byte-identical)? [Measurability, Spec §SC-002]
- [x] CHK021 - Is graceful degradation expressed measurably (0 crashes / no raw traceback across categories)? [Measurability, Spec §SC-003]
- [x] CHK022 - Is the clone-to-run target quantified (< 5 minutes) rather than "quick"? [Measurability, Spec §SC-005, README]
- [x] CHK023 - Is the performance stretch quantified with a number and marked as stretch (3,000 files < 30s)? [Measurability, Spec §SC-006, FR-014]

## Edge Case & Scenario Coverage

- [x] CHK024 - Are requirements defined for a **single file larger than the entire budget** (truncate vs exclude)? [Edge Case, Spec §FR-011, SPEC §6]
- [x] CHK025 - Are requirements defined for **budget 0 and 1** specifically? [Edge Case, Spec §Edge Cases]
- [x] CHK026 - Are requirements defined for **binary / non-UTF-8 / unreadable** files (excluded with reason)? [Edge Case, Spec §FR-006]
- [x] CHK027 - Is the **injection-text** posture specified (content treated as inert fenced data)? [Exception Flow, SPEC §12, Spec §Edge Cases]
- [x] CHK028 - Is behavior for **invalid arguments and missing/unreadable path** specified with the right codes? [Exception Flow, Spec §FR-008]
- [x] CHK029 - Is the vendored/VCS-file handling specified as listed-with-reason vs pruned? [Coverage, Spec §Clarifications]

## Dependencies & Assumptions

- [x] CHK030 - Is the stdlib-only + no-network constraint stated as a hard requirement? [Assumption, Spec §FR (constraints), SPEC §1]
- [x] CHK031 - Is the definition of "readable text file" documented (UTF-8 decode + NUL sniff)? [Assumption, Spec §Assumptions]
- [x] CHK032 - Is the assumption that budget applies to the whole rendered output (not contents) explicit? [Assumption, Spec §Assumptions]

## Ambiguities & Conflicts

- [x] CHK033 - Are there any remaining `[NEEDS CLARIFICATION]` markers or unquantified adjectives in the spec? [Ambiguity] — none remain after the 2026-07-25 clarifications session.
- [x] CHK034 - Does any requirement conflict with the fixed token rule or the absolute-budget principle? [Conflict] — none found.

## Notes

- All items checked: the spec (after the Clarifications session) specifies each invariant with a measurable,
  consistent, traceable requirement. Behavioral confirmation of these requirements lives in the 27-test suite
  (`tests/`), which is separate from this requirements-quality review.
- Verification mapping (for reference, not part of the requirements review): CHK019→test_rank_budget,
  CHK020→test_determinism, CHK021/026/027→test_walk_noise, CHK024/025→test_manifest+test_edgecases,
  CHK028→test_cli, CHK002→test_edgecases (many files).
