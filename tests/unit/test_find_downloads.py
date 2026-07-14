from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from hpr.find_downloads import latest_reengagement_csv


class DownloadsTests(unittest.TestCase):
    def test_latest_reengagement_csv_selects_newest_valid_file(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            old = root / "Re-Engagement old.csv"
            new = root / "Re-Engagement new.csv"
            ignored = root / "~$Re-Engagement temp.csv"
            old.write_text("old", encoding="utf-8")
            new.write_text("new", encoding="utf-8")
            ignored.write_text("ignored", encoding="utf-8")
            old_time = 1_700_000_000
            new_time = old_time + 10
            old.touch()
            new.touch()
            ignored.touch()
            import os

            os.utime(old, (old_time, old_time))
            os.utime(new, (new_time, new_time))
            os.utime(ignored, (new_time + 10, new_time + 10))

            self.assertEqual(latest_reengagement_csv(root), new)

    def test_latest_reengagement_csv_returns_none_when_no_match(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Other.csv").write_text("x", encoding="utf-8")

            self.assertIsNone(latest_reengagement_csv(root))

    def test_latest_reengagement_csv_breaks_tied_timestamps_deterministically(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "Re-Engagement A.csv"
            second = root / "Re-Engagement B.csv"
            first.write_text("a", encoding="utf-8")
            second.write_text("b", encoding="utf-8")
            import os

            tied = 1_700_000_000
            os.utime(first, (tied, tied))
            os.utime(second, (tied, tied))

            self.assertEqual(latest_reengagement_csv(root), second)


if __name__ == "__main__":
    unittest.main()
