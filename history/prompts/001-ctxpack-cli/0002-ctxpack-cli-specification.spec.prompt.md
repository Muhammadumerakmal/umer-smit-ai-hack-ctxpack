---
id: 0002
title: ctxpack CLI Specification
stage: spec
date: 2026-07-25
surface: agent
model: claude-opus-4-8
feature: 001-ctxpack-cli
branch: 001-ctxpack-cli
user: Muhammadaliakmal
command: /sp.specify
labels: [spec, ctxpack, cli, ranking, budget, determinism]
links:
  spec: specs/001-ctxpack-cli/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - SPEC.md
 - specs/001-ctxpack-cli/spec.md
 - specs/001-ctxpack-cli/checklists/requirements.md
 - history/prompts/001-ctxpack-cli/0002-ctxpack-cli-specification.spec.prompt.md
tests:
 - none
---

## Prompt

Feature: ctxpack — the core CLI tool. Build a Python 3.10+ standard-library-only command-line tool that recursively walks a project folder, ranks every readable text file by relevance to a free-text task description, and packs the most relevant files into a single markdown bundle that fits within a token budget (tokens = math.ceil(len(text)/4)), never exceeding it by even one token. It emits a manifest (exact schema: budget, used, included[{path,tokens,reason}], excluded[{path,reason}]) accounting for every file considered.

CLI contract (exact, hidden tests bind to it): ctxpack --path <folder> --task "<desc>" --budget <int> [--out <file>] [--manifest <file>]. Exit codes: 0 success, 1 invalid arguments, 2 path not found/unreadable. --out omitted → stdout; --manifest omitted → one-line summary to stderr.

The SPEC.md MUST document, before any code: (a) CLI contract + exit-code behavior; (b) ranking strategy and WHY over rejected alternatives (candidates: filename/path match with task keywords, keyword overlap of file content with task, directory depth, import graph, recency); (c) truncation policy — what happens when a file doesn't fit the remaining budget (head slice / smart slice / exclude); (d) noise detection — how generated/vendored files are excluded WITHOUT hardcoding a name list; (e) budget-spending decision — whether a project structure tree is worth its tokens; (f) definition of done.

Requirements: MUST recursively walk and consider every readable text file; MUST rank by task relevance; MUST never exceed budget; MUST produce complete manifest; MUST handle non-text/unreadable/non-UTF8 files without crashing; MUST be deterministic (byte-identical repeat output — all ordering explicitly sorted); MUST fail clearly with one-line errors and correct exit codes. SHOULD exclude noise (.git, node_modules, lockfiles, build artifacts) and say so; SHOULD handle a too-large file intelligently; SHOULD include a project structure overview if justified. STRETCH: respect .gitignore; run 3000 files in under 30s. Architecture must be modular (separable ranking, truncation, noise, budgeting, rendering units) to absorb a mid-hackathon curveball requirement cleanly. Hidden test categories: empty/near-empty inputs, single file larger than budget, tiny budgets, binary/non-UTF8 files, very many files, prompt-injection text in files, invalid args/missing paths, repeat-run byte-identical output.

## Response snapshot

Created feature branch `001-ctxpack-cli` and authored two spec artifacts:

1. `specs/001-ctxpack-cli/spec.md` — SDD-template spec: 3 prioritized user stories (pack-within-budget P1,
   survive-adversarial-input P1, defend-decisions P2), edge cases mapped 1:1 to every hidden-test category,
   15 functional requirements (FR-001..FR-015), key entities, and 6 measurable success criteria including
   100%-never-exceed-budget and byte-identical repeat runs.

2. `SPEC.md` (repo root — the graded deliverable, commit #1, no code) — full engineering decisions with
   rejected alternatives:
   - Ranking: task-keyword path+content weighted score; cheaper-wins tie-break; path-sorted for determinism.
     Rejected import-graph (brittle/over-engineered), recency (breaks determinism), name-only or content-only.
   - Truncation: head-slice with marker gated by minimum-useful-slice threshold; rejected smart-slice
     (language-specific) and blind exclude (wastes budget).
   - Noise: structural signals (NUL/decode-fail, entropy/line-shape, vendored dirs) not a hardcoded name list.
   - Budget spending: tree only when proportionally affordable; dropped on tiny budgets.
   - Architecture: 8 separable units (walk/noise/rank/budget/truncate/render/manifest/cli) to absorb curveball.
   - Determinism rules, injection posture (content is inert data), exact manifest schema, definition of done.

Also wrote `specs/001-ctxpack-cli/checklists/requirements.md` — all quality-checklist items pass, zero
[NEEDS CLARIFICATION] markers.

## Outcome

- ✅ Impact: Graded SPEC.md ready as first commit (spec only, no code) — satisfies the 20% spec-quality gate.
- 🧪 Tests: none yet (spec phase); acceptance scenarios defined for the test phase.
- 📁 Files: SPEC.md, specs/001-ctxpack-cli/spec.md, checklists/requirements.md, this PHR.
- 🔁 Next prompts: /sp.plan to produce the implementation plan and module design.
- 🧠 Reflection: Kept ranking simple and defensible (viva-ready) over clever; determinism enforced by explicit sort keys.

## Evaluation notes (flywheel)

- Failure modes observed: create-new-feature.ps1 emitted a cosmetic ParameterBindingException after
  successfully creating the branch and spec file — verified state directly; no impact.
- Graders run and results (PASS/FAIL): requirements checklist — all PASS.
- Prompt variant (if applicable): N/A.
- Next experiment (smallest change to try): /sp.plan, then commit SPEC.md + constitution as commit #1.
