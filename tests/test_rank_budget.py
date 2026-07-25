"""Ranking order and the absolute budget ceiling."""

import tempfile
import unittest
from pathlib import Path

from tests._util import count_tokens, load_manifest, make_tree, run_cli


class TestBudget(unittest.TestCase):
    def _run(self, files, task, budget):
        d = tempfile.mkdtemp()
        make_tree(Path(d), files)
        out = Path(d) / "b.md"
        man = Path(d) / "m.json"
        code, _, _ = run_cli(["--path", d, "--task", task, "--budget", str(budget),
                              "--out", str(out), "--manifest", str(man)])
        return code, out, man

    def test_budget_never_exceeded(self):
        files = {f"f{i}.py": ("x = %d\n" % i) * 50 for i in range(20)}
        for budget in (0, 1, 5, 50, 200, 1000):
            code, out, man = self._run(files, "x", budget)
            self.assertEqual(code, 0)
            bundle = out.read_text(encoding="utf-8")
            self.assertLessEqual(count_tokens(bundle), budget,
                                 f"budget {budget} exceeded: {count_tokens(bundle)}")
            self.assertEqual(load_manifest(man)["used"], count_tokens(bundle))

    def test_used_matches_bundle_tokens(self):
        code, out, man = self._run({"a.py": "print('hello world')\n" * 10}, "hello", 1000)
        self.assertEqual(load_manifest(man)["used"],
                         count_tokens(out.read_text(encoding="utf-8")))


class TestRanking(unittest.TestCase):
    def test_relevant_file_included_first(self):
        d = tempfile.mkdtemp()
        make_tree(Path(d), {
            "auth.py": "def login(user):\n    return authenticate(user)\n" * 3,
            "unrelated.py": "def add(a, b):\n    return a + b\n" * 3,
        })
        man = Path(d) / "m.json"
        # Budget only large enough for one file -> the relevant one must win.
        code, _, _ = run_cli(["--path", d, "--task", "fix the login authentication",
                              "--budget", "60", "--manifest", str(man)])
        self.assertEqual(code, 0)
        m = load_manifest(man)
        included_paths = [e["path"] for e in m["included"]]
        self.assertIn("auth.py", included_paths)
        self.assertNotIn("unrelated.py", included_paths)


if __name__ == "__main__":
    unittest.main()
