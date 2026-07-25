"""Shared test helpers for the ctxpack suite (standard library only)."""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CTXPACK = REPO_ROOT / "ctxpack.py"


def run_cli(args, cwd=None, py_flags=None):
    """Invoke `python [py_flags] ctxpack.py <args>` as a real subprocess.

    Returns (returncode, stdout_bytes, stderr_text). Using a subprocess exercises
    the true entry point, exit codes, and byte-exact stdout (for determinism).
    `py_flags` (e.g. ["-O"]) are passed to the interpreter itself.
    """
    cmd = [sys.executable, *(py_flags or []), str(CTXPACK), *args]
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.returncode, proc.stdout, proc.stderr.decode("utf-8", "replace")


def make_tree(root: Path, files: dict) -> None:
    """Create files under root. `files` maps relative POSIX path -> bytes or str."""
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content, encoding="utf-8")


def count_tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
