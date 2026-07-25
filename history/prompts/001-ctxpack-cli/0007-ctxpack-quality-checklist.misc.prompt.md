---
id: 0007
title: ctxpack Quality Checklist
stage: misc
date: 2026-07-25
surface: agent
model: claude-opus-4-8
feature: 001-ctxpack-cli
branch: main
user: muhammadumerakmal
command: /sp.checklist
labels: [checklist, quality, requirements, ctxpack]
links:
  spec: specs/001-ctxpack-cli/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/001-ctxpack-cli/checklists/quality.md
 - history/prompts/001-ctxpack-cli/0007-ctxpack-quality-checklist.misc.prompt.md
tests:
 - none
---

## Prompt

Generate a quality/validation checklist for the ctxpack feature (001-ctxpack-cli). Focus on the hackathon's hidden-test categories and constitutional invariants as verifiable checklist items: budget never exceeded (complete rendered bundle, tokens=ceil(len/4)); deterministic byte-identical repeat runs; stdlib-only + no network; exit codes 0/1/2 with one-line errors and no tracebacks; manifest exact schema with complete disjoint accounting; graceful handling of empty/near-empty, single-file-over-budget, tiny budgets (0/1), binary/non-UTF8, many files, injection-text-inert, invalid args/missing path; noise detection via structural signals; head-slice truncation with marker; clone-to-run under 5 minutes; graded artifacts present (SPEC.md, README.md, CLAUDE.md, PROMPTS.md, JOURNAL.md). Make items testable/checkable and map each to how it is verified (which test or manual check).

## Response snapshot

Generated `specs/001-ctxpack-cli/checklists/quality.md` — 34 requirements-quality items (CHK001–CHK034)
framed as "unit tests for English" (validating that requirements are complete/clear/consistent/measurable, NOT
testing code). Grouped by dimension: Completeness, Clarity, Consistency, Acceptance Criteria Quality, Edge Case
& Scenario Coverage, Dependencies & Assumptions, Ambiguities & Conflicts. >80% items carry spec traceability
(§FR-xxx, §SC-xxx, §Clarifications, contracts, SPEC sections). All items checked as satisfied post-clarification.

Included a non-normative verification mapping (CHK→test file) in Notes for the team's convenience, while keeping
the checklist itself focused on requirement quality per the skill's core principle. No clarifying questions were
needed — the user's focus areas were explicit.

## Outcome

- ✅ Impact: Confirms the spec is a well-formed basis for the hidden tests — no vague adjectives, no open markers.
- 🧪 Tests: none (requirements review); behavioral coverage cross-referenced to the 27-test suite.
- 📁 Files: specs/001-ctxpack-cli/checklists/quality.md, this PHR.
- 🔁 Next prompts: /sp.analyze for cross-artifact consistency.
- 🧠 Reflection: Reframed the user's "map to which test" ask into requirements-quality items + a separate verification map, honoring the checklist's purpose.

## Evaluation notes (flywheel)

- Failure modes observed: none.
- Graders run and results (PASS/FAIL): checklist self-review — all 34 items satisfied.
- Prompt variant (if applicable): N/A.
- Next experiment (smallest change to try): /sp.analyze.
