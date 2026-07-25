# PROMPTS.md — the 5 most important prompts

**Project:** ctxpack · **Author:** Muhammad Umar Akmal (solo)

The five prompts that most shaped the tool. For each: what I asked Claude Code, what it returned, and what I
changed or kept and why.

---

## Prompt 1 — Turn the brief into a constitution

**Asked**: Convert the hackathon brief into a project constitution of non-negotiable principles — spec-first,
determinism, standard-library-only/offline, graceful degradation, the absolute token budget, defensible
decisions, "you own every line", and the fixed token rule.

**Got back**: `.specify/memory/constitution.md` v1.0.0 — eight principles mapped 1:1 onto the grading axes, plus
a technical-constraints section (CLI contract, exit codes, manifest schema).

**Kept / why**: Kept it as-is and used it as the checklist I validated every later step against. The
"budget is absolute" and "determinism" principles became hard gates I re-checked on every change.

---

## Prompt 2 — Write SPEC.md before any code

**Asked**: Write `SPEC.md` documenting the exact CLI contract, my ranking strategy **with the alternatives I
rejected and why**, the truncation policy, noise detection without a hardcoded name list, the budget-spending
decision (is a tree worth its tokens?), and a definition of "done".

**Got back**: A structured spec with a decision table (why not an import graph, why not file recency, etc.).

**Changed / why**: I committed this **first, with no implementation code**, to satisfy the spec-quality gate
(20% of the grade, timestamp-checked). During planning I tightened the budget section to state the
character-equivalence trick — `ceil(len/4) ≤ budget` iff `len ≤ budget×4` — which later made the budget guarantee
exact instead of approximate.

---

## Prompt 3 — Implement, with the budget enforced in characters

**Asked**: Build `ctxpack.py` (single file, stdlib only) plus a `unittest` suite; count tokens with one
`ceil(len/4)` function used everywhere, and guarantee the rendered bundle never exceeds the budget by even one token.

**Got back**: A working implementation whose key move was enforcing the budget in **characters**
(`len(bundle) ≤ budget×4`) so the ceiling is exact and additive — no per-block rounding drift.

**Changed / why**: This replaced a naive "add up each file's token count" approach that can drift a token per file
because `ceil` isn't additive. Enforcing in characters is what makes "never exceed by one token" provable, and I
kept it because I could explain exactly why it's correct.

---

## Prompt 4 — One test per hidden-test category

**Asked**: Write a test for every hidden-test category in the brief — empty/near-empty input, a single file
larger than the budget, tiny budgets (0 and 1), binary/non-UTF-8 files, very many files, injection text kept
inert, invalid args / missing path, and byte-identical repeat runs.

**Got back**: A `unittest` suite (subprocess-driven so it exercises the real CLI, exit codes, and byte output).

**Changed / why**: I added a determinism test that runs the CLI twice and diffs the raw bytes — the single most
valuable guard for the "repeat runs" category. Running the suite (not just reading the code) is how I verified
each guarantee actually held.

---

## Prompt 5 — Review the code with sub-agents, then fix what they found

**Asked**: Run specialised review agents (silent-failure, Python, and security reviewers) against `ctxpack.py`
and fix the real findings.

**Got back**: Three concrete, verified bugs I had not spotted: a **markdown fence breakout** (a file containing
a ``` line could smuggle live "instruction" headings into the bundle — defeating the injection-inert
requirement), **symlink following** (a symlinked file could disclose data outside `--path`), and **unbounded
memory** on a huge file. The security agent even built a working proof-of-concept for the fence breakout.

**Changed / why**: I applied the fixes I could defend — a dynamic fence (longest backtick run + 1), refusing to
follow symlinks, a per-file size cap, `os.walk(onerror=…)`, and replacing the budget `assert` with an explicit
`raise` so it survives `python -O` — and added `tests/test_security.py` (suite went from 27 to **31** tests, all
green). I deliberately **rejected** one suggestion (switching ranking to word-boundary matching) because `\b`
boundaries break on snake_case identifiers like `auth_service`, so substring matching is the better choice for a
code tool. This prompt is also my Journal Q3 answer: clean, confident-looking code was still wrong until I ran it
and had it reviewed.
