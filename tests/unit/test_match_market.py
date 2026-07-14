from __future__ import annotations

import unittest
from datetime import date

from hpr.errors import InputValidationError, MarketInferenceError
from hpr.match_market import normalize_market_name
from hpr.report.build import report_file_name


class MarketAndFilenameTests(unittest.TestCase):
    def test_supported_alias_normalizes_to_canonical_market(self) -> None:
        self.assertEqual(normalize_market_name("LBR"), "Baton Rouge")
        self.assertEqual(normalize_market_name("St Louis"), "St. Louis")

    def test_unknown_manual_market_is_rejected(self) -> None:
        with self.assertRaises(MarketInferenceError):
            normalize_market_name("../bad")

    def test_report_filename_uses_readable_safe_market_component(self) -> None:
        self.assertEqual(
            report_file_name("Baton Rouge", date(2026, 6, 1)),
            "Baton Rouge - Hosted Players Report 06.01.26.xlsx",
        )

    def test_report_filename_rejects_windows_reserved_device_name(self) -> None:
        with self.assertRaises(InputValidationError):
            report_file_name("CON", date(2026, 6, 1))

    def test_report_filename_rejects_path_components(self) -> None:
        with self.assertRaises(InputValidationError):
            report_file_name("..\\Bad", date(2026, 6, 1))


if __name__ == "__main__":
    unittest.main()
