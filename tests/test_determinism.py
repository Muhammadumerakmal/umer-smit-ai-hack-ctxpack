"""Byte-identical repeat runs (bundle and manifest)."""

import tempfile
import unittest
from pathlib import Path

from tests._util import make_tree, run_cli


class TestDeterminism(unittest.TestCase):
    def test_repeat_runs_byte_identical(self):
        d = tempfile.mkdtemp()
        make_tree(Path(d), {
            "src/auth.py": "def login():\n    return authenticate()\n" * 5,
            "src/util.py": "def helper():\n    return 42\n" * 5,
            "docs/readme.md": "# Title\n\nSome docs about login.\n" * 3,
            "data.bin": b"\x00\x01\x02",
        })

        def once():
            out = Path(tempfile.mktemp())
            man = Path(tempfile.mktemp())
            code, _, _ = run_cli(["--path", d, "--task", "fix login authentication",
                                  "--budget", "500", "--out", str(out), "--manifest", str(man)])
            self.assertEqual(code, 0)
            return out.read_bytes(), man.read_bytes()

        b1, m1 = once()
        b2, m2 = once()
        self.assertEqual(b1, b2, "bundle bytes differ between runs")
        self.assertEqual(m1, m2, "manifest bytes differ between runs")


if __name__ == "__main__":
    unittest.main()
