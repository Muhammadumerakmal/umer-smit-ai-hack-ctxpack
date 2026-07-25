"""CLI contract: exit codes and stdout/stderr routing."""

import tempfile
import unittest
from pathlib import Path

from tests._util import make_tree, run_cli


class TestCliExitCodes(unittest.TestCase):
    def test_missing_budget_is_exit_1(self):
        with tempfile.TemporaryDirectory() as d:
            code, _, err = run_cli(["--path", d, "--task", "x"])
            self.assertEqual(code, 1)
            self.assertIn("ctxpack: error:", err)

    def test_non_integer_budget_is_exit_1(self):
        with tempfile.TemporaryDirectory() as d:
            code, _, err = run_cli(["--path", d, "--task", "x", "--budget", "abc"])
            self.assertEqual(code, 1)
            self.assertIn("non-negative integer", err)

    def test_negative_budget_is_exit_1(self):
        with tempfile.TemporaryDirectory() as d:
            code, _, err = run_cli(["--path", d, "--task", "x", "--budget", "-5"])
            self.assertEqual(code, 1)

    def test_missing_path_is_exit_2(self):
        code, _, err = run_cli(["--path", "no_such_dir_xyz", "--task", "x", "--budget", "100"])
        self.assertEqual(code, 2)
        self.assertIn("path not found", err)

    def test_file_as_path_is_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "a.txt"
            f.write_text("hello", encoding="utf-8")
            code, _, err = run_cli(["--path", str(f), "--task", "x", "--budget", "100"])
            self.assertEqual(code, 2)
            self.assertIn("not a directory", err)

    def test_success_is_exit_0(self):
        with tempfile.TemporaryDirectory() as d:
            make_tree(Path(d), {"a.py": "print('hi')\n"})
            code, out, err = run_cli(["--path", d, "--task", "print", "--budget", "1000"])
            self.assertEqual(code, 0)
            self.assertIn(b"a.py", out)

    def test_no_traceback_ever(self):
        code, _, err = run_cli(["--path", "no_such_dir", "--task", "x", "--budget", "100"])
        self.assertNotIn("Traceback", err)


class TestCliRouting(unittest.TestCase):
    def test_out_file_receives_bundle_stdout_empty(self):
        with tempfile.TemporaryDirectory() as d:
            make_tree(Path(d), {"a.py": "print('hi')\n"})
            out_file = Path(d) / "bundle.md"
            code, out, err = run_cli(
                ["--path", d, "--task", "print", "--budget", "1000", "--out", str(out_file)])
            self.assertEqual(code, 0)
            self.assertEqual(out, b"")                      # nothing on stdout
            self.assertIn("a.py", out_file.read_text(encoding="utf-8"))

    def test_summary_to_stderr_when_no_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            make_tree(Path(d), {"a.py": "print('hi')\n"})
            code, out, err = run_cli(["--path", d, "--task", "print", "--budget", "1000"])
            self.assertIn("tokens,", err)
            self.assertIn("included,", err)

    def test_manifest_file_and_clean_stderr(self):
        with tempfile.TemporaryDirectory() as d:
            make_tree(Path(d), {"a.py": "print('hi')\n"})
            man = Path(d) / "m.json"
            code, out, err = run_cli(
                ["--path", d, "--task", "print", "--budget", "1000", "--manifest", str(man)])
            self.assertEqual(code, 0)
            self.assertEqual(err, "")                       # nothing on stderr on success
            self.assertTrue(man.exists())


if __name__ == "__main__":
    unittest.main()
