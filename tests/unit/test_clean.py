from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from hpr.clean import clean_runtime_artifacts


class RuntimeCleanTests(unittest.TestCase):
    def test_clean_removes_only_runtime_cache_artifacts(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            cache = root / "hpr" / "__pycache__"
            cache.mkdir(parents=True)
            (cache / "module.cpython-311.pyc").write_bytes(b"cache")
            (root / ".DS_Store").write_text("junk", encoding="utf-8")
            keep = root / "outputs" / "report.xlsx"
            keep.parent.mkdir()
            keep.write_text("keep", encoding="utf-8")

            removed = clean_runtime_artifacts(root)

            self.assertEqual(removed, 2)
            self.assertFalse(cache.exists())
            self.assertFalse((root / ".DS_Store").exists())
            self.assertTrue(keep.exists())


if __name__ == "__main__":
    unittest.main()
