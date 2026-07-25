# Quickstart — ctxpack (clone to first run in <5 min)

## Requirements

- Python 3.10 or newer. Nothing else — standard library only, runs fully offline.

Check:
```bash
python --version   # must be >= 3.10
```

## Run it

From the repo root:

```bash
python ctxpack.py --path ./sample_project --task "fix the authentication bug" --budget 8000
```

- The **bundle** prints to stdout (redirect with `--out bundle.md`).
- A **one-line summary** prints to stderr (write full JSON with `--manifest manifest.json`).

Write both to files:

```bash
python ctxpack.py --path ./sample_project --task "add rate limiting" --budget 8000 \
  --out bundle.md --manifest manifest.json
```

## Verify the core guarantees

Budget is never exceeded (tokens = ceil(chars/4)):
```bash
python ctxpack.py --path ./sample_project --task "x" --budget 500 --out b.md
python -c "import math;print(math.ceil(len(open('b.md',encoding='utf-8').read())/4))"   # <= 500
```

Deterministic (byte-identical repeat runs):
```bash
python ctxpack.py --path ./sample_project --task "x" --budget 4000 --out a.md
python ctxpack.py --path ./sample_project --task "x" --budget 4000 --out b.md
diff a.md b.md && echo "identical"
```

Exit codes:
```bash
python ctxpack.py --path ./sample_project --task "x"; echo $?        # 1 (missing --budget)
python ctxpack.py --path ./does-not-exist --task "x" --budget 100; echo $?   # 2
```

## Run the tests

```bash
python -m unittest discover -s tests -v
```

## Optional: install as a command

```bash
pip install -e .        # provides `ctxpack` on PATH (optional; not required for judging)
ctxpack --path . --task "overview" --budget 6000
```
