from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

from hpr.clipboard import ClipboardResult, copy_text_to_clipboard


class ClipboardTests(unittest.TestCase):
    def test_failed_platform_command_continues_to_tk_fallback(self) -> None:
        with (
            patch("hpr.clipboard.platform.system", return_value="Darwin"),
            patch(
                "hpr.clipboard.subprocess.run",
                side_effect=subprocess.CalledProcessError(1, ["pbcopy"]),
            ),
            patch(
                "hpr.clipboard._copy_with_tkinter",
                return_value=ClipboardResult(True, "tk copied"),
            ) as tk_copy,
        ):
            result = copy_text_to_clipboard("100")

        self.assertTrue(result.copied)
        self.assertEqual(result.message, "tk copied")
        tk_copy.assert_called_once_with("100")

    def test_all_clipboard_failures_include_platform_and_tk_context(self) -> None:
        with (
            patch("hpr.clipboard.platform.system", return_value="Windows"),
            patch(
                "hpr.clipboard.subprocess.run",
                side_effect=OSError("clip missing"),
            ),
            patch(
                "hpr.clipboard._copy_with_tkinter",
                return_value=ClipboardResult(False, "tk failed"),
            ),
        ):
            result = copy_text_to_clipboard("100")

        self.assertFalse(result.copied)
        self.assertIn("clip missing", result.message)
        self.assertIn("tk failed", result.message)

    def test_platform_only_clipboard_does_not_call_tk_fallback(self) -> None:
        with (
            patch("hpr.clipboard.platform.system", return_value="Windows"),
            patch(
                "hpr.clipboard.subprocess.run",
                side_effect=OSError("clip missing"),
            ),
            patch("hpr.clipboard._copy_with_tkinter") as tk_copy,
        ):
            result = copy_text_to_clipboard("100", use_tk_fallback=False)

        self.assertFalse(result.copied)
        self.assertIn("clip missing", result.message)
        tk_copy.assert_not_called()


if __name__ == "__main__":
    unittest.main()
