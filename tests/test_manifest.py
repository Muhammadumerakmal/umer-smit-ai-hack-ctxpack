"""Manifest schema, complete accounting, and truncation marker."""

import tempfile
import unittest
from pathlib import Path

from tests._util import count_tokens, load_manifest, make_tree, run_cli


class TestManifest(unittest.TestCase):
    def _run(self, files, task, budget):
        d = tempfile.mkdtemp()
        make_tree(Path(d), files)
        man = Path(d) / "m.json"
        out = Path(d) / "b.md"
        code, _, err = run_cli(["--path", d, "--task", task, "--budget", str(budget),
                                "--manifest", str(man), "--out", str(out)])
        self.assertEqual(code, 0, err)
        return load_manifest(man), out.read_text(encoding="utf-8")

    def test_exact_schema_keys(self):
        m, _ = self._run({"a.py": "print(1)\n"}, "print", 1000)
        self.assertEqual(set(m.keys()), {"budget", "used", "included", "excluded"})
        for e in m["included"]:
            self.assertEqual(set(e.keys()), {"path", "tokens", "reason"})
        for e in m["excluded"]:
            self.assertEqual(set(e.keys()), {"path", "reason"})

    def test_single_file_larger_than_budget_truncates_or_excludes(self):
        big = "line of source code number\n" * 500  # far bigger than budget
        m, bundle = self._run({"big.py": big}, "source code", 200)
        self.assertLessEqual(count_tokens(bundle), 200)
        # Either truncated-and-included, or excluded with a reason -- never a crash.
        if m["included"]:
            self.assertIn("truncated", m["included"][0]["reason"])
            self.assertIn("[truncated:", bundle)
        else:
            self.assertTrue(m["excluded"])

    def test_excluded_sorted_by_path(self):
        m, _ = self._run({
            "z.bin": b"\x00", "a.bin": b"\x00", "m.bin": b"\x00", "keep.py": "x=1\n",
        }, "x", 1000)
        paths = [e["path"] for e in m["excluded"]]
        self.assertEqual(paths, sorted(paths))


if __name__ == "__main__":
    unittest.main()
