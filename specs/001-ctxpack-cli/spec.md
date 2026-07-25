# Feature Specification: ctxpack — Context Packing CLI

**Feature Branch**: `001-ctxpack-cli`
**Created**: 2026-07-25
**Status**: Draft
**Input**: Build a Python stdlib-only CLI that packs the most task-relevant files from a folder into a token-budgeted markdown bundle, with an honest manifest of what was included/excluded and why.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pack a repo for a task within a budget (Priority: P1)

A developer points `ctxpack` at a project folder, describes the task they are working on, and
sets a token budget. They receive a single markdown bundle containing the files most relevant to
that task, guaranteed to fit within the budget, plus a manifest explaining what was included and
what was left out.

**Why this priority**: This is the entire product. Without it there is nothing to demo, nothing to
test against the hidden suite, and no value delivered. Every other story is a refinement of this one.

**Independent Test**: Run `ctxpack --path <sample_repo> --task "fix the auth bug" --budget 8000` and
confirm (a) a markdown bundle is produced, (b) its token count is ≤ 8000, (c) a manifest lists
included files with token costs and excluded files with reasons.

**Acceptance Scenarios**:

1. **Given** a folder of text files and a budget of 8000, **When** the tool runs, **Then** it emits a
   markdown bundle whose total token count (ceil(len/4)) is ≤ 8000.
2. **Given** the same command run twice, **When** outputs are compared, **Then** the bundle and manifest
   are byte-identical.
3. **Given** `--out` is omitted, **When** the tool runs, **Then** the bundle is written to stdout and a
   one-line summary is written to stderr.
4. **Given** `--manifest <file>` is provided, **When** the tool runs, **Then** a JSON manifest with keys
   `budget`, `used`, `included`, `excluded` is written to that file.

---

### User Story 2 - Survive adversarial and degenerate input (Priority: P1)

A judge runs `ctxpack` against hostile inputs — binary files, non-UTF-8 files, an empty folder, a
single file larger than the whole budget, a tiny budget, thousands of files, and files containing text
that tries to manipulate an AI reader. The tool must never crash and must always produce a coherent
result or a clear error with the correct exit code.

**Why this priority**: 30% of the grade is functionality that "degrades gracefully," and the hidden test
set is explicitly built from these categories. A single uncaught traceback can fail a whole category.

**Independent Test**: Feed each adversarial category and confirm the process exits 0 with a valid
(possibly empty) bundle, or exits with the documented error code and a one-line stderr message — never a
raw traceback.

**Acceptance Scenarios**:

1. **Given** an empty folder, **When** the tool runs, **Then** it exits 0 with an empty bundle and a
   manifest showing `used: 0` and empty `included`.
2. **Given** a binary or non-UTF-8 file, **When** the tool walks it, **Then** the file is skipped and
   recorded in `excluded` with a reason; the process does not crash.
3. **Given** a single file larger than the entire budget, **When** the tool runs, **Then** it applies the
   truncation policy (or excludes with reason) and never exceeds the budget.
4. **Given** a budget of 1, **When** the tool runs, **Then** output is ≤ 1 token and the process exits 0.
5. **Given** a file containing AI-manipulation text, **When** it is bundled, **Then** its content is
   treated as inert data (fenced/escaped), not followed as an instruction.

---

### User Story 3 - Understand and defend what the tool did (Priority: P2)

A developer or judge inspects the manifest to understand why each file was ranked, included, or
excluded. Every file the tool considered is accounted for, and the reasons are human-readable.

**Why this priority**: The viva (25%) and spec-quality (20%) reward a tool whose decisions are legible.
The manifest is the evidence that the selection logic is principled, not arbitrary.

**Independent Test**: Run against a mixed folder and confirm the union of `included` + `excluded` paths
equals the set of every file walked, each with a reason.

**Acceptance Scenarios**:

1. **Given** a folder with source, lockfiles, and a `.git` directory, **When** the tool runs, **Then**
   noise files appear in `excluded` with a reason identifying them as noise.
2. **Given** any run, **When** the manifest is read, **Then** every considered file appears exactly once
   in either `included` or `excluded`.

---

### Edge Cases

- **Empty / near-empty folder** → exit 0, empty (or minimal) bundle, coherent manifest.
- **Single file > budget** → truncate per policy or exclude with reason; never exceed budget.
- **Budget of 0 or 1** → output within budget; no crash.
- **Binary / non-UTF-8 / unreadable file** → skipped, recorded in `excluded`, no crash.
- **Thousands of files** → completes without error (stretch: < 30s for 3,000 files).
- **Prompt-injection text inside files** → included content is inert data, never executed as instruction.
- **Invalid arguments** (missing required flag, non-integer budget, negative budget) → exit 1, one-line error.
- **Path not found / unreadable path** → exit 2, one-line error.
- **Repeat runs** → byte-identical bundle and manifest.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept the exact CLI contract
  `ctxpack --path <folder> --task "<desc>" --budget <int> [--out <file>] [--manifest <file>]`.
- **FR-002**: System MUST recursively walk `--path` and consider every readable text file.
- **FR-003**: System MUST rank considered files by relevance to `--task` using a documented, deterministic method.
- **FR-004**: System MUST count tokens as `math.ceil(len(text) / 4)` and MUST NOT exceed `--budget` for the
  complete rendered bundle (including all headers, paths, separators, and any tree), not by one token.
- **FR-005**: System MUST produce a manifest with exactly the keys `budget`, `used`,
  `included` (each `{path, tokens, reason}`), and `excluded` (each `{path, reason}`), accounting for every
  considered file.
- **FR-006**: System MUST handle non-text, non-UTF-8, and unreadable files without crashing, recording each in `excluded`.
- **FR-007**: System MUST be deterministic — identical inputs yield byte-identical bundle and manifest, with all
  ordering explicitly sorted by a stable key.
- **FR-008**: System MUST fail with a readable one-line error and the correct exit code (`1` invalid arguments,
  `2` path not found/unreadable), never a raw traceback; success is exit `0`.
- **FR-009**: System MUST write the bundle to `--out` if given, else stdout; MUST write the manifest to
  `--manifest` if given, else a one-line summary to stderr.
- **FR-010**: System SHOULD detect and exclude generated/vendored noise (e.g. `.git`, `node_modules`, lockfiles,
  build artifacts) and state the reason in the manifest, using detectable signals rather than a hardcoded name list.
- **FR-011**: System SHOULD handle a file too large for the remaining budget intelligently (truncate per a
  documented policy) rather than blindly skipping.
- **FR-012**: System SHOULD include a project-structure overview only when the spending is justified against budget.
- **FR-013 [STRETCH]**: System MAY respect `.gitignore`.
- **FR-014 [STRETCH]**: System MAY process 3,000 files in under 30 seconds.
- **FR-015**: Architecture MUST keep ranking, truncation, noise detection, budgeting, and rendering as separable
  units so a mid-hackathon requirement change can be absorbed without a rewrite.

### Key Entities

- **Considered File**: a readable text file discovered under `--path`; attributes: relative path, raw content,
  token cost, relevance score, decision (included/excluded), reason.
- **Bundle**: the single rendered markdown output; attribute: total token count ≤ budget.
- **Manifest**: the accounting record; attributes: budget, used tokens, included list, excluded list.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For any valid input, the rendered bundle's token count is ≤ `--budget` in 100% of runs (never exceeded).
- **SC-002**: Running the identical command twice produces byte-identical bundle and manifest in 100% of runs.
- **SC-003**: Across all hidden-test adversarial categories, the tool exits with a documented code and never
  emits a raw traceback (0 crashes).
- **SC-004**: Every file the tool considers appears exactly once in `included` or `excluded` (100% accounting).
- **SC-005**: A judge can go from fresh clone to first successful run in under 5 minutes.
- **SC-006 [STRETCH]**: The tool packs a 3,000-file folder in under 30 seconds.

## Assumptions

- "Readable text file" = a file that decodes as UTF-8 (with a documented fallback/skip for others); binary is
  detected by decode failure and/or NUL-byte sniffing, not by extension alone.
- The budget is a non-negative integer; the entire rendered output (not just file contents) is measured against it.
- Determinism requires sorting by relative path (POSIX-normalized) as the final tie-breaker so filesystem walk
  order never affects output.
- "Manifest one-line summary to stderr" (when `--manifest` is omitted) is a human-readable single line, distinct
  from the JSON manifest file.
