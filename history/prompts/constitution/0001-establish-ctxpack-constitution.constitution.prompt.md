---
id: 0001
title: Establish ctxpack Constitution
stage: constitution
date: 2026-07-25
surface: agent
model: claude-opus-4-8
feature: none
branch: master
user: Muhammadaliakmal
command: /sp.constitution
labels: [constitution, ctxpack, sdd, hackathon]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - .specify/memory/constitution.md
 - history/prompts/constitution/0001-establish-ctxpack-constitution.constitution.prompt.md
tests:
 - none
---

## Prompt

Project: ctxpack — a Python standard-library-only CLI that packs the most relevant files from a code folder into a token-budgeted markdown bundle, with an honest manifest of what was included/excluded and why. Principles must cover: (1) Spec-driven development is mandatory — first commit is SPEC.md only, spec is a graded deliverable; (2) Determinism — same command twice yields byte-identical output; (3) Python stdlib only, no third-party packages, no network calls at runtime; (4) Graceful degradation — never crash on binary/unreadable/non-UTF8 files, empty inputs, tiny budgets; fail with clear one-line errors and correct exit codes (0 success, 1 invalid args, 2 path not found); (5) Never exceed the token budget by even one token; (6) Every engineering decision (ranking, truncation, noise detection, budget spending) must be defensible; (7) You own every line — understandability over cleverness; (8) Token counting rule is fixed: math.ceil(len(text)/4).

## Response snapshot

Authored `.specify/memory/constitution.md` at version 1.0.0 (initial ratification) with eight
non-negotiable principles derived from the ctxpack hackathon brief:

1. Spec-Driven Development (NON-NEGOTIABLE) — first commit is SPEC.md only; spec is graded.
2. Deterministic Output (NON-NEGOTIABLE) — byte-identical repeat runs; all ordering explicitly sorted.
3. Standard Library Only, Offline — Python 3.10+ stdlib, no third-party, no network at runtime.
4. Graceful Degradation & Honest Failure — no crashes on adversarial input; one-line errors, right exit codes.
5. The Budget Is Absolute — entire rendered output must fit --budget, never exceed by one token.
6. Every Decision Is Defensible — ranking/truncation/noise/budget choices documented with rejected alternatives.
7. You Own Every Line — understandability over cleverness; must be explainable in viva.
8. Fixed Token-Counting Rule — tokens = math.ceil(len(text)/4), applied uniformly.

Added Technical Constraints (CLI contract, exit codes 0/1/2, manifest schema) and Development
Workflow & Quality Gates (spec-first, incremental commits, curveball-absorbing architecture).
Included Sync Impact Report as leading HTML comment. Verified plan-template.md references the
constitution generically, so no template edits required.

## Outcome

- ✅ Impact: Project constitution ratified at v1.0.0; foundation for spec-first workflow set.
- 🧪 Tests: none (governance artifact).
- 📁 Files: .specify/memory/constitution.md (written), this PHR.
- 🔁 Next prompts: /sp.specify to author SPEC.md (must be first git commit, no code).
- 🧠 Reflection: 8 principles map 1:1 onto the brief's grading axes (functionality, determinism, spec quality, defensibility, ownership).

## Evaluation notes (flywheel)

- Failure modes observed: none.
- Graders run and results (PASS/FAIL): N/A.
- Prompt variant (if applicable): N/A.
- Next experiment (smallest change to try): Draft SPEC.md and commit it alone as commit #1.
