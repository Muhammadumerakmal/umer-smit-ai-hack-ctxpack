<!--
SYNC IMPACT REPORT
==================
Version change: (unversioned template) → 1.0.0
Bump rationale: MAJOR — initial ratification of a concrete constitution from template.

Modified principles: (all newly defined from placeholders)
  [PRINCIPLE_1_NAME] → I. Spec-Driven Development (NON-NEGOTIABLE)
  [PRINCIPLE_2_NAME] → II. Deterministic Output (NON-NEGOTIABLE)
  [PRINCIPLE_3_NAME] → III. Standard Library Only, Offline
  [PRINCIPLE_4_NAME] → IV. Graceful Degradation & Honest Failure
  [PRINCIPLE_5_NAME] → V. The Budget Is Absolute
  [PRINCIPLE_6_NAME] → VI. Every Decision Is Defensible
  (added)           → VII. You Own Every Line
  (added)           → VIII. Fixed Token-Counting Rule

Added sections:
  - Technical Constraints (CLI contract, exit codes, manifest schema)
  - Development Workflow & Quality Gates

Removed sections: none (all template placeholders resolved)

Templates requiring updates:
  ✅ .specify/memory/constitution.md (this file)
  ⚠ .specify/templates/plan-template.md — verify "Constitution Check" gate references these principles
  ⚠ .specify/templates/spec-template.md — ensure SPEC.md mandatory sections align (ranking/truncation/noise/done)
  ⚠ .specify/templates/tasks-template.md — ensure determinism + graceful-degradation task types present

Follow-up TODOs: none. RATIFICATION_DATE set to first-authoring date.
-->

# ctxpack Constitution

`ctxpack` is a Python command-line tool that takes a folder of code, a task description,
and a token budget, then produces the single best context bundle that fits inside that
budget — plus an honest manifest of what it left out and why. These principles are
non-negotiable and supersede convenience.

## Core Principles

### I. Spec-Driven Development (NON-NEGOTIABLE)
The specification is written before any implementation code exists. The first git commit
MUST contain `SPEC.md` and no implementation code — commit timestamps are evidence and are
checked. `SPEC.md` MUST state, before building: the CLI contract and exit-code behavior,
the ranking strategy and why it was chosen over rejected alternatives, the truncation
policy, what counts as noise and how it is detected, and the definition of "done". The spec
is a graded deliverable, not documentation written afterward; it is updated as work
proceeds and those updates MUST be visible in git history.

### II. Deterministic Output (NON-NEGOTIABLE)
The same command run twice against the same inputs MUST produce byte-identical output —
both the bundle and the manifest. No wall-clock timestamps, no unordered set/dict iteration,
no randomness, no reliance on filesystem walk order. All ordering (file walk, ranking ties,
manifest entries) MUST be explicitly sorted by a stable, documented key. Determinism is
directly tested at judging via repeat runs.

### III. Standard Library Only, Offline
Only the Python 3.10+ standard library may be used. No third-party packages, no `pip install`
of a solution. `ctxpack` MUST run fully offline: zero network calls at runtime. This forces
the selection logic to be genuinely built, not imported.

### IV. Graceful Degradation & Honest Failure
`ctxpack` MUST NOT crash on adversarial or degenerate input: binary files, non-UTF-8 files,
unreadable files, empty folders, near-empty folders, a single file larger than the whole
budget, extremely small budgets, huge file counts, and files containing text designed to
manipulate an AI reader. Malformed input MUST produce a readable one-line error on stderr
and the correct exit code — never a raw traceback. Every considered file appears in the
manifest: included with its token cost, or excluded with a reason.

### V. The Budget Is Absolute
The complete bundle output MUST NOT exceed `--budget` by even one token. The budget applies
to the entire rendered output — headers, file paths, separators, tree diagrams, everything —
not merely the file contents. When a file does not fit, the truncation policy defined in the
spec applies; blind skipping is not automatically acceptable and must be justified.

### VI. Every Decision Is Defensible
Ranking, truncation, noise detection, and budget spending are deliberate engineering choices
with no single right answer. For each, the chosen approach MUST be documented alongside the
alternatives rejected and the reason. A decision that cannot be defended in the live viva
scores nothing regardless of whether the code works.

### VII. You Own Every Line
Any team member may be asked to explain any file. Understandability outranks cleverness:
prefer clear, boring code over clever code that no one can defend. "The AI wrote it" is not
an explanation. If a construct cannot be explained by its author, it does not belong in the
submission.

### VIII. Fixed Token-Counting Rule
Token counting is fixed and identical for every team: `tokens = math.ceil(len(text) / 4)`.
No `tiktoken`, no API calls, no alternative heuristic. This rule is applied uniformly to all
text whose tokens are counted, including bundle scaffolding, so that the absolute budget in
Principle V is measured consistently.

## Technical Constraints

**CLI contract (implement exactly — hidden tests bind to it):**
```
ctxpack --path <folder> --task "<task description>" --budget <int> [--out <file>] [--manifest <file>]
```
- `--path` (required): folder to pack.
- `--task` (required): free-text description of the developer's goal.
- `--budget` (required): maximum tokens for the entire bundle.
- `--out` (optional): write bundle here; if omitted, write to stdout.
- `--manifest` (optional): write manifest JSON here; if omitted, print a one-line summary to stderr.

**Exit codes:** `0` success · `1` invalid arguments · `2` path not found or unreadable.

**Manifest schema (exact keys):**
```json
{
  "budget": 8000,
  "used": 7912,
  "included": [{"path": "src/agent.py", "tokens": 812, "reason": "..."}],
  "excluded": [{"path": "package-lock.json", "reason": "..."}]
}
```

**Runtime:** Python 3.10+, runs on a clean machine via `python ctxpack.py ...` or an
installed entry point. A judge MUST get from clone to first run in under 5 minutes.

## Development Workflow & Quality Gates

- **Spec first.** No implementation code may be committed before `SPEC.md`.
- **Incremental commits.** History shows evolution — small, meaningful commits, not one dump.
- **Graded artifacts.** `SPEC.md`, `CLAUDE.md`, `PROMPTS.md`, and `JOURNAL.md` are deliverables
  and MUST be maintained as first-class work, not afterthoughts.
- **Absorb the curveball.** A required specification change arrives mid-hackathon. Architecture
  MUST be structured so a new requirement can be absorbed without a rewrite: keep ranking,
  truncation, noise detection, budgeting, and rendering as separable, replaceable units.
- **Verify what comes back.** Output from Claude Code is checked against these principles before
  it is kept; anything unexplainable or non-deterministic is rejected.

## Governance

This constitution supersedes all other practices for `ctxpack`. Amendments MUST be documented
in the Sync Impact Report at the top of this file, versioned per the policy below, and
propagated to dependent templates (`plan-template.md`, `spec-template.md`, `tasks-template.md`).

**Versioning policy (semantic):**
- MAJOR: backward-incompatible governance or principle removal/redefinition.
- MINOR: a new principle or section, or materially expanded guidance.
- PATCH: clarifications, wording, and non-semantic refinements.

**Compliance:** Every change is reviewed against these principles. Principle I (spec-first),
Principle II (determinism), and Principle V (absolute budget) are hard gates — a violation of
any blocks the change. Complexity MUST be justified against Principle VII.

**Version**: 1.0.0 | **Ratified**: 2026-07-25 | **Last Amended**: 2026-07-25
