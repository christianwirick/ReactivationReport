from __future__ import annotations

import unittest
from datetime import date

from openpyxl import Workbook

from hpr.report.build import add_hosted_report_sheets
from tests.fixtures.report_data import hosted_row


class FormulaSafetyTests(unittest.TestCase):
    def test_user_controlled_text_cells_are_neutralized(self) -> None:
        workbook = Workbook()
        add_hosted_report_sheets(
            workbook=workbook,
            market="Baton Rouge",
            report_date=date(2026, 6, 1),
            hosted_rows=[
                hosted_row(
                    **{
                        "Current Host Name": "+Host",
                        "Name Full": "=cmd()",
                        "Tier": "@Tier",
                        "Last 90 ADT": -12.5,
                        "Total Theo ": 50,
                    }
                )
            ],
        )

        detail = workbook["Baton Rouge"]
        self.assertEqual(detail["B2"].value, "'+Host")
        self.assertEqual(detail["E2"].value, "'=cmd()")
        self.assertEqual(detail["F2"].value, "'@Tier")
        self.assertEqual(detail["L2"].value, -12.5)
        self.assertEqual(detail["M2"].value, 50)

        summary = workbook["Summary"]
        self.assertEqual(summary["B2"].value, "As of Monday, June 1, 2026")
        self.assertEqual(summary["B6"].value, "'+Host")
        workbook.close()


if __name__ == "__main__":
    unittest.main()
