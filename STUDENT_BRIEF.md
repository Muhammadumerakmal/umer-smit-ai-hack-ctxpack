# Module 1 Hackathon — `ctxpack`

**Build the tool you've been learning to use.**

---

## The Situation

Every AI coding assistant has the same bottleneck: the context window. Point Claude Code at a large repository and it cannot read everything — something has to decide what goes in and what gets left out. Right now, that "something" is usually a developer guessing.

Your job is to replace the guessing with a tool. You will build `ctxpack`: a Python command-line tool that takes a folder of code, a description of the task at hand, and a token budget — and produces the single best context bundle that fits inside that budget, plus an honest account of what it left out and why.

This is context engineering as a product. You have been the user of it all module. Today you build it.

---

## What You Must Build

A Python CLI called `ctxpack` that, given a project folder and a token budget, selects and packs the most relevant files into one markdown bundle that fits the budget — and reports what it included, what it excluded, and why.

---

## Mandatory Requirements

### The CLI contract — implement this exactly

Hidden tests are run against this interface. Deviate and the tests fail.

```
ctxpack --path <folder> --task "<task description>" --budget <int> [--out <file>] [--manifest <file>]
```

| Flag | Behavior |
|---|---|
| `--path` | Folder to pack. Required. |
| `--task` | Free-text description of what the developer is trying to do. Required. |
| `--budget` | Maximum tokens for the **entire** bundle. Required. |
| `--out` | Write bundle here. If omitted, write to stdout. |
| `--manifest` | Write manifest JSON here. If omitted, print a one-line summary to stderr. |

**Exit codes:** `0` success · `1` invalid arguments · `2` path not found or unreadable.

### Token counting — use exactly this rule

```python
tokens = math.ceil(len(text) / 4)
```

No tiktoken, no API calls. Every team counts identically so results are comparable. The budget applies to the **complete bundle output**, including any headers, file paths, separators, or tree diagrams you add — not just the file contents.

### Manifest schema — these exact keys

```json
{
  "budget": 8000,
  "used": 7912,
  "included": [{"path": "src/agent.py", "tokens": 812, "reason": "..."}],
  "excluded": [{"path": "package-lock.json", "reason": "..."}]
}
```

### Requirements list

1. **[MUST]** Recursively walk `--path` and consider every readable text file.
2. **[MUST]** Rank files by relevance to `--task`. The ranking method is your decision — defend it in your spec.
3. **[MUST]** Never exceed `--budget`. Not by one token.
4. **[MUST]** Produce a manifest accounting for every file considered: included with token cost, or excluded with a reason.
5. **[MUST]** Handle non-text and unreadable files without crashing.
6. **[MUST]** Be deterministic — the same command twice produces byte-identical output.
7. **[MUST]** Fail clearly. Bad input gets a readable one-line error and the right exit code, never a raw traceback.
8. **[SHOULD]** Exclude obvious noise (`.git`, `node_modules`, lockfiles, build artifacts) and say so in the manifest.
9. **[SHOULD]** Handle a file too large for the remaining budget intelligently rather than skipping blindly.
10. **[SHOULD]** Include a project structure overview in the bundle — if you can justify spending budget on it.
11. **[STRETCH]** Respect `.gitignore`.
12. **[STRETCH]** Run on 3,000 files in under 30 seconds.

### Spec-driven development — enforced, not suggested

**Your first git commit must contain `SPEC.md` and no implementation code.** Commit timestamps are checked at judging. A repo whose first commit is working code scores zero on Spec Quality — 20% of the total — no matter how good the tool is.

Your `SPEC.md` must state, before you build:
- The CLI contract and exit code behavior
- Your ranking strategy and **why** you chose it over the alternatives you considered
- Your truncation policy: what happens when a file doesn't fit
- What counts as noise and how you detect it
- Your definition of "done"

The spec is a graded deliverable. It is not documentation written afterward.

### Decisions we are deliberately not making for you

There is no single right answer to these. Pick one, write down what you rejected, and be ready to defend it:

1. **Ranking.** Filename matching? Keyword overlap with `--task`? Directory depth? Import graph? File recency? Something else?
2. **Truncation.** A 5,000-token file with 2,000 tokens of budget left — include the head, include a smart slice, or exclude it entirely?
3. **Noise.** How do you detect a generated file without hardcoding a list of names?
4. **Budget spending.** Is a directory tree worth 300 tokens that could have been source code?

Two teams choosing opposite answers can both score full marks. A team that cannot say why scores nothing here.

---

## Constraints

- **Python standard library only.** No third-party packages. This is a deliberate constraint — it removes the "pip install a solution" path and makes you build the selection logic yourself.
- **No network calls at runtime.** `ctxpack` must run fully offline.
- **Claude Code is required**, not optional. Your `CLAUDE.md` and your driving prompts are graded artifacts.
- **Python 3.10+**, runs on a clean machine with `python ctxpack.py ...` or an installed entry point. Your README must get a judge from clone to first run in under 5 minutes.

---

## What You Submit

| Deliverable | Notes |
|---|---|
| **Git repo** | Full history. First commit = `SPEC.md` only. Incremental commits, not one dump at the end. |
| **`SPEC.md`** | Written first. Updated as you go — updates are expected and visible in history. |
| **Working CLI** | Runs from a fresh clone against a folder the judges provide. |
| **`CLAUDE.md`** | The context file you used to drive Claude Code. This is a context engineering artifact and it is graded. |
| **`PROMPTS.md`** | Your 5 most important prompts. For each: what you asked, what you got back, what you changed and why. |
| **`JOURNAL.md`** | One page. Five questions, answered below. |
| **3-minute demo** | Live, at judging. |

### `JOURNAL.md` — answer these five

1. Three decisions we made, and what we rejected in each case.
2. The hardest bug we hit, and how we found the root cause.
3. **Something Claude Code got wrong or confidently misled us on, and how we caught it.**
4. What we would do differently with two more hours.
5. Who wrote what — per person.

Question 3 matters most. Every team that actually worked with the tool has a specific answer.

---

## How You'll Be Judged

| Criterion | Weight |
|---|---|
| Functionality — passes the hidden test set, degrades gracefully | 30 |
| Understanding — the live viva | 25 |
| Spec quality & engineering decisions — is the spec real, and did you follow it? | 20 |
| Curveball response | 15 |
| Demo, README, and journal | 10 |

**Understanding gates everything.** If no member of your team can explain a component, that component contributes **zero** to Functionality even if it works perfectly.

### The hidden test set

Your tool will be run at judging against a test folder you have not seen. You get the categories, not the cases:

- Empty and near-empty inputs
- A single file larger than the entire budget
- Extremely small budgets
- Binary and non-UTF-8 files
- Very large numbers of files
- Files containing text designed to manipulate an AI reading it
- Invalid arguments and missing paths
- Repeat runs, checked for byte-identical output

Build for these categories. You cannot guess the cases.

---

## Rules on AI Use

**Claude Code is not just allowed — it is the point of this module, and you are expected to use it heavily.**

And: **you own every line you submit.**

Any team member may be asked to explain any part of your code during judging. Judges pick the person and pick the file — you do not nominate a speaker. *"The AI wrote it"* is not an answer. A team that cannot explain its own submission loses the entire Understanding score regardless of whether the product works.

The teams that do well today will not be the ones who prompt the most. They will be the ones who specified clearly, gave Claude Code the right context, checked what came back, and knew why they kept it.

---

## Timeline (2-hour format)

| Time | Event |
|---|---|
| 0:00 | Kickoff, brief released, questions |
| 0:00 – 0:18 | **Spec phase.** Write `SPEC.md`. Commit it. No code yet. |
| 0:24 | **Checkpoint 1** — mentors review your spec and architecture in 60 seconds |
| 0:54 | **Checkpoint 2** — something must run end to end, however thin |
| 1:12 | **Curveball released** — same for every team, announced live and in writing |
| 1:15 | **Checkpoint 3** — you have a plan for the curveball |
| 1:48 | **Checkpoint 4** — fresh-clone check: does your README actually work? |
| 1:54 | Submission freeze — final push |
| 1:54 – onwards | Judging: demo, hidden tests, viva |

There is a required change to the specification coming at 1:12. Its content is not announced in advance. Architecture that absorbs it cleanly is architecture that was understood.

---

## Starter Materials

- A sample project folder for local testing — **note: this is not the hidden test set**
- `README_TEMPLATE.md`
- `SPEC_TEMPLATE.md`

---

## Scaling the Format

| Duration | Scope |
|---|---|
| 6 hours | MUSTs 1–7 only. Drop the SHOULDs. Curveball at hour 4. |
| 10 hours | This brief as written. |
| 24 hours | Add all STRETCH items, plus a required test suite the team writes themselves. |
| 48 hours | Add a second interface — a `ctxpack` MCP server exposing the same selection logic as a tool. |

---

## One Last Thing

You have spent this module learning to give an AI good context. Today, the quality of the context **you** give Claude Code determines the quality of the tool you ship for giving context to Claude Code.

Do it well and you will feel the loop close.
