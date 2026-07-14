from __future__ import annotations

import sys
import types
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

from hpr.excel.build_pivots import _decorate_summary_sheet, create_native_summary_pivot


class ExcelAutomationTeardownTests(unittest.TestCase):
    def test_native_summary_uses_the_shared_date_label(self) -> None:
        worksheet = MagicMock()
        cells: dict[str, MagicMock] = {}
        worksheet.Range.side_effect = lambda address: cells.setdefault(address, MagicMock())

        _decorate_summary_sheet(worksheet, "Summary", date(2026, 6, 1), "D")

        self.assertEqual(cells["B2"].Value, "As of Monday, June 1, 2026")

    def test_quit_failure_does_not_mask_degraded_result_and_coinitialize_cleanup_runs(self) -> None:
        fake_pythoncom = _FakePythoncom()
        fake_excel = _FakeExcel()
        fake_client = types.ModuleType("win32com.client")
        fake_client.DispatchEx = lambda _name: fake_excel
        fake_win32com = types.ModuleType("win32com")
        fake_win32com.client = fake_client

        with (
            patch("hpr.excel.build_pivots.platform.system", return_value="Windows"),
            patch.dict(
                sys.modules,
                {
                    "pythoncom": fake_pythoncom,
                    "win32com": fake_win32com,
                    "win32com.client": fake_client,
                },
            ),
        ):
            result = create_native_summary_pivot(
                workbook_path=Path("report.xlsx"),
                market_sheet="Baton Rouge",
                report_date=date(2026, 6, 1),
            )

        self.assertFalse(result.created)
        self.assertIn("does not contain 'Baton Rouge'", result.message)
        self.assertNotIn("quit failed", result.message)
        self.assertTrue(fake_excel.quit_called)
        self.assertTrue(fake_pythoncom.uninitialized)


class _FakePythoncom(types.ModuleType):
    def __init__(self) -> None:
        super().__init__("pythoncom")
        self.initialized = False
        self.uninitialized = False

    def CoInitialize(self) -> None:
        self.initialized = True

    def CoUninitialize(self) -> None:
        self.uninitialized = True


class _FakeWorksheets:
    Count = 0

    def __call__(self, _index):
        raise AssertionError("No worksheets should be requested when Count is zero")


class _FakeWorkbook:
    def __init__(self) -> None:
        self.Worksheets = _FakeWorksheets()
        self.close_calls: list[bool] = []

    def Close(self, *, SaveChanges: bool) -> None:
        self.close_calls.append(SaveChanges)


class _FakeWorkbooks:
    def __init__(self, workbook: _FakeWorkbook) -> None:
        self.workbook = workbook

    def Open(self, *_args, **_kwargs) -> _FakeWorkbook:
        return self.workbook


class _FakeExcel:
    def __init__(self) -> None:
        self.workbook = _FakeWorkbook()
        self.Workbooks = _FakeWorkbooks(self.workbook)
        self.quit_called = False

    def Quit(self) -> None:
        self.quit_called = True
        raise RuntimeError("quit failed")


if __name__ == "__main__":
    unittest.main()
