# JOURNAL.md

*(One page. Seeded from the build session — replace bracketed team-specific parts before submission.)*

## 1. Three decisions we made, and what we rejected

- **Ranking = task-keyword path+content score.** Rejected an **import-graph** ranker (language-specific,
  brittle on partial repos, hard to make deterministic and to defend in a viva) and **file recency/mtime**
  (not reproducible across clones — it would break byte-identical repeat runs).
- **Truncation = head-slice with a visible marker**, gated by a minimum-useful-slice threshold. Rejected a
  semantic "smart slice" (needs per-language parsing = more code to own and more determinism surface) and
  blind exclusion (wastes budget when a file's top is its most informative part).
- **Noise detection = structural signals**, not a hardcoded filename list. Rejected a pure name allowlist
  because it misses generated files it has never seen; we keep a small vendored-dir set only as a convenience
  prior, with the real gate being decode-failure / line-shape / lockfile-shape.

## 2. The hardest bug we hit, and how we found the root cause

**[Team: confirm/replace.]** The subtle one was the **budget ceiling**: summing per-file token counts
(`ceil(len/4)` each) and adding them can drift above the true bundle token count, because `ceil` is not
additive — the concatenated bundle can round differently than the sum of parts. Root cause found by reasoning
about the token rule: since `tokens = ceil(len/4)`, `ceil(len/4) ≤ budget` **iff** `len ≤ budget×4`. Switching
budget enforcement to **characters** made the "never exceed by one token" guarantee exact and killed the drift.

## 3. Something Claude Code got wrong or confidently misled us on, and how we caught it

**[Team: put your real answer here — this question is worth the most.]** Candidate from this session: the
initial `pyproject.toml` declared the console-script entry point as `ctxpack:main_console`, but the module only
defined `main(argv)` — the installed `ctxpack` command would have failed at runtime. We caught it by reading the
entry-point contract (console scripts call a **zero-argument** function) and added a `main_console()` wrapper.
Lesson: generated glue code (packaging, entry points) needs the same verification as core logic.

## 4. What we would do differently with two more hours

- Add `.gitignore`-awareness (STRETCH) and a proper "smart slice" that prefers imports/definitions.
- Add a performance pass + timing assertion for the 3,000-file case (currently we assert completion, not <30s).
- Add an aggregate-bytes circuit breaker (we added a per-file 5 MB cap; a whole-tree cap would bound memory further).

> Note: a review pass (silent-failure / python / security review agents) hardened the tool against a markdown
> fence-breakout injection, symlink exfiltration, oversized-file memory DoS, and the `assert`-under-`-O` gap —
> those are now fixed and covered by `tests/test_security.py`, not left for "two more hours".

## 5. Who wrote what — per person

**[Team: fill in per person. Judges pick the file and the speaker — everyone must be able to explain any part.]**

- `ctxpack.py` (walk / noise / rank / budget / truncate / render / manifest / cli): [name(s)]
- Tests (`tests/`): [name(s)]
- SPEC / plan / constitution: [name(s)]
- README / packaging: [name(s)]
