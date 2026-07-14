from __future__ import annotations

import inspect
import unittest

from hpr.gui.app import HostedPlayersReportApp
from hpr.gui.state import GuiState


class _FakeStringVar:
    def __init__(self, value: str) -> None:
        self.value = value

    def set(self, value: str) -> None:
        self.value = value


class GuiSuccessLayoutTests(unittest.TestCase):
    def test_step_one_primary_button_uses_sentence_case(self) -> None:
        source = inspect.getsource(HostedPlayersReportApp.render_inputs)

        self.assertIn("Find reactivated players", source)
        self.assertNotIn("Find Reactivated Players", source)

    def test_success_screen_keeps_details_behind_qa_report_button(self) -> None:
        source = inspect.getsource(HostedPlayersReportApp.render_done)

        self.assertIn("QA report", source)
        self.assertIn("Open workbook", source)
        self.assertIn("Start over", source)
        self.assertIn("Close", source)
        self.assertIn("Reactivated players", source)
        self.assertNotIn("Open folder", source)
        self.assertNotIn("Copy diagnostic ID", source)
        self.assertNotIn('("Report date"', source)
        self.assertNotIn('("Missing prior-workbook rows"', source)
        self.assertNotIn('("Reconciliation"', source)
        self.assertNotIn('("Native PivotTables"', source)
        self.assertNotIn('("Theme"', source)
        self.assertNotIn('("Diagnostic ID"', source)

    def test_start_over_clears_step_one_file_selections(self) -> None:
        app = object.__new__(HostedPlayersReportApp)
        app.hosted_var = _FakeStringVar("hosted.csv")
        app.lastweek_var = _FakeStringVar("prior.xlsx")
        app.data = GuiState(
            hosted_path="hosted.csv",
            lastweek_path="prior.xlsx",
            market="Baton Rouge",
            missing_uids=["100"],
            missing_prior_row_count=1,
            distinct_missing_uid_count=1,
            clipboard_ok=True,
            clipboard_message="Copied",
            build_attempts=2,
        )
        rendered: list[bool] = []
        app.render_inputs = lambda: rendered.append(True)

        HostedPlayersReportApp._start_over(app)

        self.assertEqual(app.hosted_var.value, "")
        self.assertEqual(app.lastweek_var.value, "")
        self.assertIsNone(app.data.hosted_path)
        self.assertIsNone(app.data.lastweek_path)
        self.assertIsNone(app.data.market)
        self.assertEqual(app.data.missing_uids, [])
        self.assertEqual(app.data.missing_prior_row_count, 0)
        self.assertEqual(app.data.distinct_missing_uid_count, 0)
        self.assertFalse(app.data.clipboard_ok)
        self.assertEqual(app.data.clipboard_message, "")
        self.assertEqual(app.data.build_attempts, 0)
        self.assertEqual(rendered, [True])


if __name__ == "__main__":
    unittest.main()
