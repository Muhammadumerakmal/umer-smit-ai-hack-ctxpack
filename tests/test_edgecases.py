"""Empty/near-empty input, tiny budgets, and large file counts."""

import tempfile
import unittest
from pathlib import Path

from tests._util import count_tokens, load_manifest, make_tree, run_cli


class TestEdgeCases(unittest.TestCase):
    def test_empty_folder(self):
        with tempfile.TemporaryDirectory() as d:
            man = Path(d) / "m.json"
            out = Path(d) / "b.md"
            code, _, _ = run_cli(["--path", d, "--task", "anything", "--budget", "100",
                                  "--out", str(out), "--manifest", str(man)])
            self.assertEqual(code, 0)
            m = load_manifest(man)
            self.assertEqual(m["included"], [])
            self.assertEqual(m["excluded"], [])
            self.assertLessEqual(m["used"], 100)

    def test_budget_zero(self):
        with tempfile.TemporaryDirectory() as d:
            make_tree(Path(d), {"a.py": "print('x')\n"})
            out = Path(d) / "b.md"
            code, _, _ = run_cli(["--path", d, "--task", "x", "--budget", "0", "--out", str(out)])
            self.assertEqual(code, 0)
            self.assertEqual(count_tokens(out.read_text(encoding="utf-8")), 0)

    def test_budget_one(self):
        with tempfile.TemporaryDirectory() as d:
            make_tree(Path(d), {"a.py": "print('x')\n"})
            out = Path(d) / "b.md"
            code, _, _ = run_cli(["--path", d, "--task", "x", "--budget", "1", "--out", str(out)])
            self.assertEqual(code, 0)
            self.assertLessEqual(count_tokens(out.read_text(encoding="utf-8")), 1)

    def test_many_files(self):
        with tempfile.TemporaryDirectory() as d:
            files = {f"pkg/mod{i}.py": f"VALUE = {i}\n" for i in range(1500)}
            make_tree(Path(d), files)
            man = Path(d) / "m.json"
            out = Path(d) / "b.md"
            code, _, err = run_cli(["--path", d, "--task", "value", "--budget", "3000",
                                    "--out", str(out), "--manifest", str(man)])
            self.assertEqual(code, 0, err)
            m = load_manifest(man)
            self.assertEqual(len(m["included"]) + len(m["excluded"]), 1500)
            self.assertLessEqual(m["used"], 3000)


if __name__ == "__main__":
    unittest.main()
