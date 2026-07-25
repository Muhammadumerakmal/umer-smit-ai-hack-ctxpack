---
id: 0004
title: ctxpack Tasks Breakdown
stage: tasks
date: 2026-07-25
surface: agent
model: claude-opus-4-8
feature: 001-ctxpack-cli
branch: 001-ctxpack-cli
user: Muhammadaliakmal
command: /sp.tasks
labels: [tasks, ctxpack, mvp, incremental, tdd]
links:
  spec: specs/001-ctxpack-cli/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/001-ctxpack-cli/tasks.md
 - history/prompts/001-ctxpack-cli/0004-ctxpack-tasks-breakdown.tasks.prompt.md
tests:
 - none
---

## Prompt

Generate the dependency-ordered tasks.md for ctxpack from plan.md, research.md, data-model.md, contracts/cli-contract.md, and quickstart.md. Honor the constitution: spec-driven, deterministic byte-identical output, stdlib-only/offline, graceful degradation with exit codes 0/1/2, budget never exceeded, fixed token rule math.ceil(len/4), understandable code.

Sequence tasks to build the 8 separable units incrementally so there is always something runnable (Checkpoint-2 "thin end-to-end" early): (1) project scaffolding; (2) count_tokens + argparse CLI with exit-code mapping and stdout/stderr routing — thin end-to-end empty bundle+manifest; (3) walk + encoding/readability gate; (4) noise structural-signal detection; (5) rank; (6) budget greedy fill + scaffolding-first accounting; (7) truncate head-slice + min-slice gate; (8) render markdown + optional affordable tree; (9) manifest exact-schema deterministic; (10) top-level error guard. Then a test task PER hidden-test category using stdlib unittest with fixtures. Finish with README, PROMPTS.md and JOURNAL.md stubs. Mark [P] parallelizable, note test-first (red). Each task: clear acceptance check and file path.

## Response snapshot

Generated `specs/001-ctxpack-cli/tasks.md` — 32 tasks (T001–T032) in strict checklist format
(`- [ ] Txxx [P?] [USx?] desc + file path`), organized by phase and user story:

- Phase 1 Setup (T001–T004): ctxpack.py skeleton, tests/ pkg, README stub, optional pyproject.toml.
- Phase 2 Foundational / thin e2e (T005–T009): count_tokens, red CLI tests, argparse with exit-code override
  (arg errors→1), validate_path (→2), thin main emitting empty bundle+manifest. → Checkpoint 2.
- Phase 3 US1 MVP (T010–T016): walk, rank, render, pack (budget-absolute), manifest, wire-up, red rank/budget tests.
- Phase 4 US2 adversarial (T017–T022): encoding/readability hardening, is_noise structural signals,
  truncate_to_fit head-slice, injection-inert, top-level error guard, red walk/noise tests.
- Phase 5 US3 auditability (T023–T025): complete manifest accounting, affordable structure tree, red manifest tests.
- Phase 6 Polish (T026–T032): determinism test, edgecases test, many-files test, README finalize,
  PROMPTS.md + JOURNAL.md graded stubs, full-suite + stdlib/offline verification.

Each hidden-test category maps to a concrete test task. Dependencies, parallel opportunities, and MVP-first
strategy documented; curveball-readiness noted (change lands in one unit).

## Outcome

- ✅ Impact: Executable, dependency-ordered backlog; MVP (US1) isolated for earliest demo.
- 🧪 Tests: test tasks defined per hidden-test category (red-first where practical).
- 📁 Files: specs/001-ctxpack-cli/tasks.md, this PHR.
- 🔁 Next prompts: /sp.analyze (optional consistency check) then /sp.implement.
- 🧠 Reflection: Front-loaded a thin end-to-end so Checkpoint-2 is reachable fast; robustness layered after MVP.

## Evaluation notes (flywheel)

- Failure modes observed: none.
- Graders run and results (PASS/FAIL): format validation — all tasks conform to checklist format.
- Prompt variant (if applicable): N/A.
- Next experiment (smallest change to try): optional /sp.analyze, then /sp.implement starting at T001.
