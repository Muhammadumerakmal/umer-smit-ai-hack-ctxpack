---
id: 0003
title: ctxpack Implementation Plan
stage: plan
date: 2026-07-25
surface: agent
model: claude-opus-4-8
feature: 001-ctxpack-cli
branch: 001-ctxpack-cli
user: Muhammadaliakmal
command: /sp.plan
labels: [plan, architecture, ctxpack, determinism, modular]
links:
  spec: specs/001-ctxpack-cli/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/001-ctxpack-cli/plan.md
 - specs/001-ctxpack-cli/research.md
 - specs/001-ctxpack-cli/data-model.md
 - specs/001-ctxpack-cli/contracts/cli-contract.md
 - specs/001-ctxpack-cli/quickstart.md
 - CLAUDE.md
 - history/prompts/001-ctxpack-cli/0003-ctxpack-implementation-plan.plan.prompt.md
tests:
 - none
---

## Prompt

Produce the implementation plan for ctxpack per SPEC.md and the constitution. Constraints: Python 3.10+, standard library only, no network at runtime, deterministic byte-identical output, budget never exceeded (measured on complete rendered bundle via tokens=math.ceil(len(text)/4)), graceful degradation with exit codes 0/1/2.

Design the modular architecture as separable units so the mid-hackathon curveball lands in one place: cli (argparse, exit codes, stdout/stderr routing), walk (recursive discovery + encoding/readability gate), noise (structural-signal detection — NUL/decode-fail, entropy/line-shape, vendored dirs), rank (task-keyword path+content weighted scoring, deterministic tie-break by token-cost then POSIX path), budget (greedy fill + absolute ceiling enforcement, scaffolding budgeted first), truncate (head-slice with marker gated by minimum-useful-slice threshold), render (markdown bundle + optional structure tree only when proportionally affordable), manifest (exact schema budget/used/included/excluded, deterministic ordering). Single-file entry point ctxpack.py runnable as `python ctxpack.py ...` plus optional installed entry point.

Plan must cover: module boundaries and function signatures, data flow, determinism strategy (explicit sort keys everywhere, no timestamps/randomness/mtime), the token-budget accounting order (scaffolding first then greedy fill), error handling and exit-code mapping, and a test plan aligned to hidden-test categories (empty/near-empty, single file > budget, tiny budgets, binary/non-UTF8, many files, injection text treated as inert data, invalid args/missing path, repeat-run byte-identical). Keep the smallest viable design; flag any architecturally significant decisions for a possible ADR.

## Response snapshot

Authored the full plan and Phase 0/1 artifacts:

- `plan.md` — Technical Context (Python 3.10+, stdlib-only, unittest, offline, deterministic), Constitution
  Check table (all 8 principles PASS, no violations), single-project structure (ctxpack.py at root + tests/),
  architecture with function signatures for the 8 separable units, data flow, determinism strategy
  (total-order sort key (-score, tokens, posix_path); no time/rand/mtime; \n normalization; fixed JSON key
  order), token-budget accounting order (scaffolding budgeted first, then greedy fill, final assert-and-trim),
  error/exit-code mapping table (0/1/2; argparse default 2 overridden to 1 for arg errors), and a test plan
  mapping 1:1 to hidden-test categories.
- `research.md` — 8 decisions (R1 ranking, R2 truncation, R3 noise, R4 tree spend, R5 token rule, R6 argparse
  exit codes, R7 determinism, R8 unittest) each with rationale + rejected alternatives; flags R1–R3 as a
  grouped ADR candidate.
- `data-model.md` — FileRec, Args, Manifest, Bundle structures with invariants (union==considered, disjoint;
  used<=budget).
- `contracts/cli-contract.md` — test-binding CLI + manifest contract, stdout/stderr routing matrix, exit codes.
- `quickstart.md` — clone-to-run in <5 min with budget/determinism/exit-code verification commands.
- Ran update-agent-context.ps1 → CLAUDE.md updated with Python 3.10+ / stdlib-only context.

## Outcome

- ✅ Impact: Implementation-ready plan; architecture isolates the curveball to one unit; all gates PASS.
- 🧪 Tests: none yet; test plan defined per hidden-test category for /sp.tasks.
- 📁 Files: plan.md, research.md, data-model.md, contracts/cli-contract.md, quickstart.md, CLAUDE.md, this PHR.
- 🔁 Next prompts: /sp.tasks to generate dependency-ordered tasks; optional /sp.adr for R1–R3.
- 🧠 Reflection: Single-file design chosen for auditability under stdlib-only + clean-machine run; separability preserved via pure functions.

## Evaluation notes (flywheel)

- Failure modes observed: none.
- Graders run and results (PASS/FAIL): Constitution Check — all PASS.
- Prompt variant (if applicable): N/A.
- Next experiment (smallest change to try): /sp.tasks, then red tests per category before implementation.

## ADR suggestion

R1 (ranking), R2 (truncation), R3 (noise detection) meet all three significance tests (long-term impact,
multiple viable alternatives, cross-cutting). Grouped ADR candidate: "Selection heuristics for ctxpack".
