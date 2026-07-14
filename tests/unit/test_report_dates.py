from __future__ import annotations

import unittest
from datetime import date

import hpr.cli as cli
import hpr.gui.app as gui
from hpr.errors import InputValidationError
from hpr.report.run import REPORT_DATE_ERROR, parse_report_date


class ReportDateTests(unittest.TestCase):
    def test_cli_and_gui_use_the_shared_parser(self) -> None:
        self.assertIs(cli.parse_report_date, parse_report_date)
        self.assertIs(gui.parse_report_date, parse_report_date)

    def test_parser_accepts_all_documented_formats(self) -> None:
        expected = date(2026, 7, 13)

        self.assertEqual(parse_report_date("7/13/2026"), expected)
        self.assertEqual(parse_report_date("7.13.2026"), expected)
        self.assertEqual(parse_report_date("2026-07-13"), expected)

    def test_parser_rejects_invalid_input_with_shared_copy(self) -> None:
        with self.assertRaisesRegex(InputValidationError, REPORT_DATE_ERROR.replace(".", r"\.")):
            parse_report_date("July 13")


if __name__ == "__main__":
    unittest.main()
