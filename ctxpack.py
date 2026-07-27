#!/usr/bin/env python3
"""ctxpack -- pack the most task-relevant files from a folder into a token-budgeted
markdown bundle, with an honest manifest of what was included/excluded and why.

Standard library only. No network. Deterministic. See SPEC.md for the full contract.

Token rule (fixed): tokens = math.ceil(len(text) / 4).
Because that rule depends only on length, "bundle tokens <= budget" is exactly
equivalent to "len(bundle) <= budget * 4"; we enforce the budget in characters so
the ceiling is exact and additive (no rounding drift).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------- #
# Tunable constants (documented in SPEC.md / research.md). Kept explicit so the
# behaviour is defensible and easy to change if a curveball lands.
# --------------------------------------------------------------------------- #
W_PATH = 5.0            # weight: a task keyword appearing in the file path
W_BODY = 1.0            # weight: a distinct task keyword appearing in the content
W_DEPTH = 0.25          # small bonus for shallower files (orientation heuristic)
W_SRC_EXT = 0.5         # small bonus for source-code extensions

TREE_BUDGET_FRACTION = 0.15   # include the structure tree only if it costs <= this fraction of budget
MIN_SLICE_CHARS = 40          # a head-slice smaller than this is not worth emitting

SNIFF_BYTES = 8192      # bytes inspected for a NUL when detecting binary files
MAX_FILE_BYTES = 5 * 1024 * 1024   # per-file read cap; larger files are excluded (memory-DoS guard)

# _minified_reason thresholds (named for defensibility)
MINIFIED_AVG_LINE_LEN = 400   # average line length above which content looks minified
MINIFIED_MAX_LINES = 5        # ...and only when there are very few lines

# Directories that are conventionally generated/vendored/VCS sinks. This is a
# convenience PRIOR, not the mechanism -- the real gate is a structural signal
# (decode failure, line-shape). Files here are excluded and SAID SO in the manifest.
VENDORED_DIRS = frozenset({
    ".git", ".hg", ".svn", "node_modules", "venv", ".venv", "env",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "dist", "build", "target", "out", ".idea", ".tox", ".gradle",
    "site-packages", ".next", ".nuxt", "coverage", ".terraform",
})

SOURCE_EXTS = frozenset({
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb",
    ".c", ".h", ".cpp", ".hpp", ".cc", ".cs", ".php", ".swift", ".kt",
    ".scala", ".sh", ".sql", ".r", ".m", ".mm", ".lua", ".pl",
})

STOPWORDS = frozenset({
    "the", "a", "an", "to", "for", "of", "in", "on", "and", "or", "is",
    "are", "be", "with", "how", "do", "i", "we", "my", "our", "this",
    "that", "it", "as", "at", "by", "from", "into", "when", "add", "fix",
})


class ArgError(Exception):
    """Invalid command-line arguments -> exit code 1."""


class PathError(Exception):
    """--path missing / not a directory / unreadable -> exit code 2."""


@dataclass
class FileRec:
    """One file discovered under --path."""
    path: str                 # POSIX-relative path (forward slashes) -- deterministic sort key
    abs_path: Path
    content: str | None = None
    excluded_reason: str | None = None   # set => pre-excluded before ranking
    content_tokens: int = 0   # count_tokens(content), used as a ranking tie-breaker
    score: float = 0.0

    @property
    def is_candidate(self) -> bool:
        return self.content is not None and self.excluded_reason is None


# --------------------------------------------------------------------------- #
# Token counting -- the ONE rule, used for every measurement.
# --------------------------------------------------------------------------- #
def count_tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
@dataclass
class Args:
    path: str
    task: str
    budget: int
    out: str | None
    manifest: str | None


class _QuietParser(argparse.ArgumentParser):
    """argparse defaults to exit code 2 on argument errors; the contract wants 1.

    Override error()/exit() so argument problems raise ArgError (mapped to exit 1
    in main) instead of argparse's own SystemExit(2). --help still exits 0.
    """

    def error(self, message: str):  # noqa: D401
        raise ArgError(message)


def parse_args(argv: list[str]) -> Args:
    parser = _QuietParser(prog="ctxpack", add_help=True,
                          description="Pack a folder into a token-budgeted markdown bundle.")
    parser.add_argument("--path", required=True, help="Folder to pack.")
    parser.add_argument("--task", required=True, help="Free-text task description.")
    parser.add_argument("--budget", required=True, help="Max tokens for the entire bundle (non-negative int).")
    parser.add_argument("--out", default=None, help="Write bundle here (default: stdout).")
    parser.add_argument("--manifest", default=None, help="Write manifest JSON here (default: summary to stderr).")

    ns = parser.parse_args(argv)

    # Validate budget as a non-negative integer ourselves (clear one-line message).
    raw = str(ns.budget).strip()
    if not (raw.isdigit()):  # rejects negatives, floats, and non-numerics
        raise ArgError("--budget must be a non-negative integer")
    budget = int(raw)

    return Args(path=ns.path, task=ns.task, budget=budget, out=ns.out, manifest=ns.manifest)


def validate_path(path_str: str) -> Path:
    p = Path(path_str)
    if not p.exists():
        raise PathError(f"path not found: {path_str}")
    if not p.is_dir():
        raise PathError(f"path is not a directory: {path_str}")
    if not os.access(p, os.R_OK):
        raise PathError(f"path is not readable: {path_str}")
    return p


# --------------------------------------------------------------------------- #
# walk -- discovery + encoding/readability gate + path-signal noise
# --------------------------------------------------------------------------- #
def _vendored_reason(rel_posix: str) -> str | None:
    parts = rel_posix.split("/")
    for seg in parts[:-1]:  # any ancestor directory
        if seg in VENDORED_DIRS:
            return f"vendored/generated directory ({seg})"
    return None


def _lockfile_reason(rel_posix: str) -> str | None:
    name = rel_posix.rsplit("/", 1)[-1].lower()
    if name.endswith(".lock") or "-lock." in name or name in {"package-lock.json", "yarn.lock", "poetry.lock", "pnpm-lock.yaml"}:
        return "lockfile / generated (low-signal) content"
    return None


def _minified_reason(content: str) -> str | None:
    if not content:
        return None
    lines = content.split("\n")
    non_empty = [ln for ln in lines if ln.strip()]
    if not non_empty:
        return None
    avg_len = sum(len(ln) for ln in non_empty) / len(non_empty)
    # A handful of extremely long lines is the signature of a minified/generated asset.
    if avg_len > MINIFIED_AVG_LINE_LEN and len(non_empty) <= MINIFIED_MAX_LINES:
        return "minified/generated asset (extreme line length)"
    return None


def walk(root: Path) -> list[FileRec]:
    """Recursively discover files. Readable UTF-8 text becomes a candidate;
    everything else is recorded with an exclusion reason. Never raises for a file."""
    recs: list[FileRec] = []

    def _on_walk_error(err: OSError) -> None:
        # os.walk defaults to onerror=None, which SILENTLY skips unreadable
        # directories -- their files would vanish from the manifest. Record them
        # instead so every path stays accounted for.
        fn = getattr(err, "filename", None) or str(root)
        try:
            drel = os.path.relpath(fn, root).replace(os.sep, "/")
        except ValueError:
            drel = str(fn)
        recs.append(FileRec(path=drel, abs_path=Path(fn),
                            excluded_reason="unreadable directory"))

    for dirpath, dirnames, filenames in os.walk(root, onerror=_on_walk_error):
        dirnames.sort()      # determinism: fix traversal order (does not affect output, but tidy)
        filenames.sort()
        for name in filenames:
            abs_path = Path(dirpath) / name
            rel = os.path.relpath(abs_path, root).replace(os.sep, "/")

            vreason = _vendored_reason(rel)
            if vreason is not None:
                recs.append(FileRec(path=rel, abs_path=abs_path, excluded_reason=vreason))
                continue

            # Do NOT follow symlinks: a symlinked file could point outside --path
            # (e.g. /etc/passwd, an SSH key). Record it, never read through it.
            if abs_path.is_symlink():
                recs.append(FileRec(path=rel, abs_path=abs_path,
                                    excluded_reason="symlink (not followed)"))
                continue

            # Size-gate BEFORE reading so a giant file can't exhaust memory.
            try:
                size = abs_path.stat().st_size
            except OSError:
                recs.append(FileRec(path=rel, abs_path=abs_path, excluded_reason="unreadable file"))
                continue
            if size > MAX_FILE_BYTES:
                recs.append(FileRec(path=rel, abs_path=abs_path,
                                    excluded_reason=f"file too large (> {MAX_FILE_BYTES // (1024 * 1024)} MB)"))
                continue

            try:
                data = abs_path.read_bytes()
            except OSError:
                recs.append(FileRec(path=rel, abs_path=abs_path, excluded_reason="unreadable file"))
                continue

            if b"\x00" in data[:SNIFF_BYTES]:
                recs.append(FileRec(path=rel, abs_path=abs_path, excluded_reason="binary or non-UTF-8"))
                continue
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                recs.append(FileRec(path=rel, abs_path=abs_path, excluded_reason="binary or non-UTF-8"))
                continue

            # Normalise line endings so output is byte-identical across OSes.
            text = text.replace("\r\n", "\n").replace("\r", "\n")

            reason = _lockfile_reason(rel) or _minified_reason(text)
            if reason is not None:
                recs.append(FileRec(path=rel, abs_path=abs_path, excluded_reason=reason))
                continue

            recs.append(FileRec(path=rel, abs_path=abs_path, content=text,
                                content_tokens=count_tokens(text)))

    recs.sort(key=lambda r: r.path)   # never depend on filesystem walk order
    return recs


# --------------------------------------------------------------------------- #
# rank -- task-keyword relevance with a deterministic total order
# --------------------------------------------------------------------------- #
def _keywords(task: str) -> list[str]:
    raw = "".join(ch.lower() if ch.isalnum() else " " for ch in task).split()
    return [w for w in raw if w not in STOPWORDS and len(w) >= 2]


def rank(files: list[FileRec], task: str) -> list[FileRec]:
    kws = _keywords(task)
    for rec in files:
        path_l = rec.path.lower()
        content_l = (rec.content or "").lower()
        path_hits = sum(path_l.count(kw) for kw in kws)
        body_distinct = sum(1 for kw in kws if kw in content_l)  # saturates at len(kws)
        depth = rec.path.count("/")
        ext = Path(rec.path).suffix.lower()
        rec.score = (
            W_PATH * path_hits
            + W_BODY * body_distinct
            + W_DEPTH * (1.0 / (1 + depth))
            + (W_SRC_EXT if ext in SOURCE_EXTS else 0.0)
        )
    # Total order: score desc, then cheaper file first (buys more), then path asc.
    return sorted(files, key=lambda r: (-r.score, r.content_tokens, r.path))


# --------------------------------------------------------------------------- #
# render / truncate / pack -- budget is absolute (enforced in characters)
# --------------------------------------------------------------------------- #
def _fence_for(body: str) -> str:
    """Return a backtick fence guaranteed longer than any backtick run in `body`.

    Without this, a file whose content contains a ``` line would close the fence
    early, letting the rest of the file render as live markdown -- an injection
    vector (attacker-authored '## SYSTEM OVERRIDE' headings become real headings).
    """
    longest = run = 0
    for ch in body:
        if ch == "`":
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    return "`" * max(3, longest + 1)


def _safe_label(path: str) -> str:
    """Neutralise characters in a filename that could break markdown structure
    when shown in a heading or the tree (backticks, newlines, carriage returns)."""
    return path.replace("`", "'").replace("\r", " ").replace("\n", " ")


def _render_block(path: str, body: str) -> str:
    fence = _fence_for(body)
    return f"## {_safe_label(path)}\n\n{fence}\n{body}\n{fence}\n\n"


def _build_tree(paths: list[str]) -> str:
    """A compact, deterministic structure overview of the given paths."""
    body_lines = []
    for p in sorted(paths):
        depth = p.count("/")
        body_lines.append("  " * depth + _safe_label(p.rsplit("/", 1)[-1]))
    body = "\n".join(body_lines)
    fence = _fence_for(body)
    return f"## Structure\n\n{fence}\n{body}\n{fence}\n\n"


def truncate_to_fit(content: str, path: str, remaining_chars: int) -> tuple[str, bool]:
    """Return (block, ok). Head-slice `content` so its rendered block fits in
    remaining_chars, appending a visible marker. ok=False if no useful slice fits.

    The rendered fence can grow if the head slice contains backtick runs, so we
    build the block and shrink the head until it provably fits -- the budget
    ceiling is absolute and must never be exceeded."""
    total_tokens = count_tokens(content)
    empty_overhead = len(_render_block(path, ""))
    marker_reserve = len(f"\n\n... [truncated: {total_tokens} of {total_tokens} tokens shown]")
    head_chars = remaining_chars - empty_overhead - marker_reserve
    while head_chars >= MIN_SLICE_CHARS:
        head = content[:head_chars]
        shown = count_tokens(head)
        marker = f"\n\n... [truncated: {shown} of {total_tokens} tokens shown]"
        block = _render_block(path, head + marker)
        if len(block) <= remaining_chars:
            return block, True
        # Fence/marker made it overflow; cut the head by the overflow and retry.
        head_chars -= max(len(block) - remaining_chars, 1)
    return "", False


def pack(ranked: list[FileRec], budget: int) -> tuple[list[dict], list[dict], str]:
    """Greedy fill under an absolute character budget (= budget * 4).

    Returns (included_entries, budget_excluded_entries, bundle_string)."""
    char_budget = budget * 4
    parts: list[str] = []
    cur = 0  # current bundle length in characters

    def fits(s: str) -> bool:
        return cur + len(s) <= char_budget

    # --- scaffolding budgeted FIRST ---
    title = "# ctxpack context bundle\n\n"
    if fits(title):
        parts.append(title)
        cur += len(title)

    tree = _build_tree([r.path for r in ranked])
    if len(tree) <= char_budget * TREE_BUDGET_FRACTION and fits(tree):
        parts.append(tree)
        cur += len(tree)

    included: list[dict] = []
    budget_excluded: list[dict] = []

    for rec in ranked:
        block = _render_block(rec.path, rec.content)
        if fits(block):
            parts.append(block)
            cur += len(block)
            included.append({"path": rec.path, "tokens": count_tokens(block),
                             "reason": "ranked relevant; full file"})
            continue
        # Doesn't fit whole -> try a head slice into whatever remains.
        remaining = char_budget - cur
        sliced, ok = truncate_to_fit(rec.content, rec.path, remaining)
        if ok and fits(sliced):
            parts.append(sliced)
            cur += len(sliced)
            included.append({"path": rec.path, "tokens": count_tokens(sliced),
                             "reason": "ranked relevant; truncated head slice to fit budget"})
        else:
            budget_excluded.append({"path": rec.path,
                                    "reason": "insufficient remaining budget"})

    bundle = "".join(parts)
    # Final guard: the invariant must hold EXACTLY. Use an explicit raise, not
    # assert -- assert statements are stripped under `python -O`/PYTHONOPTIMIZE,
    # which would silently disable the tool's single most important guarantee.
    if count_tokens(bundle) > budget:
        raise RuntimeError(
            f"budget invariant violated: {count_tokens(bundle)} > {budget}")
    return included, budget_excluded, bundle


# --------------------------------------------------------------------------- #
# manifest -- exact schema, deterministic ordering
# --------------------------------------------------------------------------- #
def build_manifest(budget: int, bundle: str, included: list[dict],
                   excluded: list[dict]) -> dict:
    excluded_sorted = sorted(excluded, key=lambda e: e["path"])
    return {
        "budget": budget,
        "used": count_tokens(bundle),
        "included": included,                 # already in render (rank) order
        "excluded": excluded_sorted,
    }


def _manifest_json(manifest: dict) -> str:
    return json.dumps(manifest, ensure_ascii=True, indent=2, separators=(",", ": "))


# --------------------------------------------------------------------------- #
# emit -- byte-exact output (no OS newline translation)
# --------------------------------------------------------------------------- #
def _write_bytes(target: str | None, text: str, default_stream) -> None:
    data = text.encode("utf-8")
    if target is None:
        default_stream.buffer.write(data)
        default_stream.buffer.flush()
    else:
        with open(target, "wb") as fh:
            fh.write(data)


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
    except ArgError as e:
        print(f"ctxpack: error: {e}", file=sys.stderr)
        return 1

    try:
        root = validate_path(args.path)
    except PathError as e:
        print(f"ctxpack: error: {e}", file=sys.stderr)
        return 2

    try:
        recs = walk(root)
        candidates = [r for r in recs if r.is_candidate]
        pre_excluded = [{"path": r.path, "reason": r.excluded_reason}
                        for r in recs if not r.is_candidate]

        ranked = rank(candidates, args.task)
        included, budget_excluded, bundle = pack(ranked, args.budget)

        manifest = build_manifest(args.budget, bundle, included,
                                  pre_excluded + budget_excluded)

        _write_bytes(args.out, bundle, sys.stdout)

        if args.manifest is not None:
            _write_bytes(args.manifest, _manifest_json(manifest) + "\n", sys.stdout)
        else:
            summary = (f"ctxpack: {manifest['used']}/{manifest['budget']} tokens, "
                       f"{len(manifest['included'])} included, "
                       f"{len(manifest['excluded'])} excluded")
            print(summary, file=sys.stderr)
        return 0
    except Exception as e:  # never leak a traceback
        # Include the exception type so an internal failure is diagnosable, while
        # still honouring the one-line-to-stderr / no-traceback contract.
        print(f"ctxpack: error: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


def main_console() -> None:
    """Zero-arg entry point for the installed `ctxpack` console script."""
    sys.exit(main(sys.argv[1:]))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
