# JOURNAL.md

**Project:** ctxpack · **Author:** Muhammad Umar Akmal (18, solo)

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

The subtle one was the **budget ceiling**: summing per-file token counts
(`ceil(len/4)` each) and adding them can drift above the true bundle token count, because `ceil` is not
additive — the concatenated bundle can round differently than the sum of parts. Root cause found by reasoning
about the token rule: since `tokens = ceil(len/4)`, `ceil(len/4) ≤ budget` **iff** `len ≤ budget×4`. Switching
budget enforcement to **characters** made the "never exceed by one token" guarantee exact and killed the drift.

## 3. Something Claude Code got wrong or confidently misled us on, and how we caught it

Claude Code wrote code that *read* very clearly and was presented with full confidence that it worked — but
when we actually **ran the script**, it didn't behave the way the explanation claimed. The clean structure and
confident tone were misleading: readable ≠ verified. We caught it by not trusting the appearance — we ran the
tool and read the code ourselves, saw the runtime behavior diverge from what was described, and pointed the
specific failure back at Claude Code, telling it to re-examine that path rather than accept its own summary.
It then found and fixed the real cause, and we re-ran to confirm.

A concrete instance is preserved in our git history: `pyproject.toml` declared the console-script entry point
as `ctxpack:main_console`, but the module only defined `main(argv)` — so the installed `ctxpack` command would
have failed at runtime even though everything *looked* correct. Console scripts call a **zero-argument**
function; checking that contract (instead of trusting the generated glue) is what surfaced it, and we added a
`main_console()` wrapper and verified it.

**The lesson we took:** Claude Code's most dangerous output is the confident, tidy-looking kind. We stopped
grading code by how clean it reads and started grading it by running it and checking behavior against the spec —
and every time behavior disagreed with the narrative, we made Claude Code re-derive from the actual failure, not
from its own prior explanation.

## 4. What we would do differently with two more hours

- Add `.gitignore`-awareness (STRETCH) and a proper "smart slice" that prefers imports/definitions.
- Add a performance pass + timing assertion for the 3,000-file case (currently we assert completion, not <30s).
- Add an aggregate-bytes circuit breaker (we added a per-file 5 MB cap; a whole-tree cap would bound memory further).

> Note: a review pass (silent-failure / python / security review agents) hardened the tool against a markdown
> fence-breakout injection, symlink exfiltration, oversized-file memory DoS, and the `assert`-under-`-O` gap —
> those are now fixed and covered by `tests/test_security.py`, not left for "two more hours".

## 5. Who wrote what — per person

Solo project — **Muhammad Umar Akmal (18)** owned the whole thing end to end. This was built as a
human-in-the-loop effort: Claude Code produced the code under my direction, and my job — the part this module
actually grades — was to specify it first, keep watch on every output, verify behavior against the spec, catch
what was wrong, and drive the iterations until it was correct.

- **Direction & specification:** wrote/approved the constitution, `SPEC.md`, plan, and tasks *before* any code,
  and kept the first commit spec-only.
- **Review & verification:** ran the tool and the test suite on each change, checked the manifest/budget/exit-code
  behavior myself, and did not accept clean-looking code until it actually ran correctly (see Q3).
- **Iteration:** pushed the tool through repeated review passes (including the silent-failure / python / security
  agents) and had each finding fixed and re-verified until the suite was green and the guarantees held.
- **Areas covered (all mine):** `ctxpack.py` (walk / noise / rank / budget / truncate / render / manifest / cli),
  the `tests/` suite, SPEC / plan / constitution, and README / packaging.

I can explain any file and any component on request.
