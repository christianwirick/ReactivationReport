from __future__ import annotations

import inspect
import unittest
from datetime import datetime
from unittest.mock import patch

from hpr.gui import text
from hpr.gui.app import HostedPlayersReportApp
from hpr.gui.state import GuiState


class _FakeStringVar:
    def __init__(self, value: str) -> None:
        self.value = value

    def set(self, value: str) -> None:
        self.value = value


class GuiSuccessLayoutTests(unittest.TestCase):
    def test_step_one_uses_report_card_copy_and_preserves_continue(self) -> None:
        source = inspect.getsource(HostedPlayersReportApp.render_inputs)

        self.assertIn("text.ADD_REPORTS_HEADING", source)
        self.assertIn("text.CONTINUE_BUTTON", source)
        self.assertEqual(text.ADD_REPORTS_HEADING, "Add files")
        self.assertEqual(text.HOSTED_PLAY_REPORT_LABEL, "90 day play report")
        self.assertNotIn("ADD_REPORTS_SUBTITLE", source)

    def test_step_one_uses_state_aware_file_card_and_settings_gear(self) -> None:
        input_source = inspect.getsource(HostedPlayersReportApp.render_inputs)

        self.assertIn("card = RoundedCard(frame, fill=CARD, border=BORDER)", input_source)
        self.assertIn("self.render_settings", input_source)
        self.assertIn("border_color=BORDER", input_source)
        self.assertIn("min_width=52", input_source)
        self.assertIn("min_height=52", input_source)
        self.assertIn('icon="gear"', input_source)
        self.assertIn('row=0, column=2, sticky="ne"', input_source)
        self.assertIn("StepNumberChip", input_source)
        self.assertIn('"✓" if selected else index', input_source)
        self.assertIn("fill=TEAL if selected else STEP_IDLE", input_source)
        self.assertIn("Path(selected_path).name", input_source)
        self.assertIn("text.HOSTED_PLAY_REPORT_HINT", input_source)
        self.assertIn("text.LAST_WEEK_WORKBOOK_HINT", input_source)
        self.assertIn("connector = TEAL if selected else STEP_IDLE", input_source)
        self.assertNotIn("RoundedEntry(", input_source)
        self.assertEqual(input_source.count('icon="folder"'), 1)
        self.assertNotIn("BROWSE_BUTTON", input_source)
        self.assertNotIn("CHANGE_FILE_BUTTON", input_source)
        self.assertIn("parent_bg=CARD", input_source)
        self.assertIn("chip.set_vertical_gradient", input_source)
        self.assertIn("GradientConnector", input_source)
        self.assertIn("FILE_CONNECTOR_GRADIENT_RANGE", input_source)
        self.assertIn("self._schedule_file_chip_gradient()", input_source)
        self.assertIn('row=4, column=0, columnspan=3, sticky="e"', input_source)

    def test_settings_is_a_distinct_page_with_visible_close_action(self) -> None:
        source = inspect.getsource(HostedPlayersReportApp.render_settings)

        self.assertIn("self._begin_step(1)", source)
        self.assertIn('self.content_shell.configure(style="Settings.TFrame")', source)
        self.assertIn("self.content_canvas.configure(bg=SETTINGS_BG)", source)
        self.assertIn('frame.configure(style="Settings.TFrame")', source)
        self.assertIn('self.footer.configure(style="Settings.TFrame")', source)
        self.assertIn('self.status_label.configure(style="SettingsSmall.TLabel")', source)
        self.assertIn('self.progress_label.configure(style="SettingsSmall.TLabel")', source)
        self.assertIn("text.SETTINGS_HEADING", source)
        self.assertIn("text.SETTINGS_SUBTITLE", source)
        self.assertIn("self.render_inputs", source)
        self.assertIn('icon="close"', source)
        self.assertIn("parent_bg=SETTINGS_BG", source)
        self.assertIn("fill=SETTINGS_CARD", source)
        self.assertIn("settings_card = RoundedCard", source)
        self.assertEqual(source.count("background=STEP_IDLE, height=1"), 2)
        self.assertIn("textvariable=self.date_var", source)
        self.assertIn("textvariable=self.outdir_var", source)
        self.assertIn("variable=self.qa_var", source)
        self.assertIn('style="SettingsCard.TCheckbutton"', source)
        self.assertIn('icon="folder"', source)
        self.assertIn("self._primary_action = self.render_inputs", source)
        self.assertIn("self._back_action = self.render_inputs", source)

        reset_source = inspect.getsource(HostedPlayersReportApp._begin_step)
        self.assertIn('self.content_shell.configure(style="TFrame")', reset_source)
        self.assertIn('self.footer.configure(style="TFrame")', reset_source)
        self.assertIn('self.status_label.configure(style="Small.TLabel")', reset_source)

    def test_wizard_uses_a_windows_safe_stable_window(self) -> None:
        init_source = inspect.getsource(HostedPlayersReportApp.__init__)
        center_source = inspect.getsource(HostedPlayersReportApp._center_window)
        chrome_source = inspect.getsource(HostedPlayersReportApp._build_chrome)

        self.assertIn("self.minsize(820, 580)", init_source)
        self.assertIn("width, height = 860, 600", center_source)
        self.assertIn("padding=(28, 20, 28, 16)", chrome_source)
        self.assertIn("padding=(28, 8, 28, 12)", chrome_source)

    def test_representative_copy_is_centralized(self) -> None:
        self.assertEqual(text.ADD_REPORTS_HEADING, "Add files")
        self.assertEqual(text.copied_uids_heading(3), "✓  3 UIDs copied to your clipboard")
        self.assertEqual(text.OPEN_WORKBOOK_BUTTON, "Open workbook")
        self.assertEqual(text.COPY_UIDS_BUTTON, "Copy UIDs")
        self.assertEqual(text.QA_OPTION, "QA mode")

    def test_step_two_success_uses_one_card_with_purple_chips_and_copy_action(self) -> None:
        source = inspect.getsource(HostedPlayersReportApp.render_clipboard)

        self.assertIn("text.copied_uids_heading", source)
        self.assertIn("GradientBanner", source)
        self.assertIn("font=self.font_heading", source)
        self.assertIn("colors=(CARD, CARD)", source)
        self.assertIn("height=68", source)
        self.assertIn("text_color=TEAL", source)
        self.assertNotIn("ShadowLabel", source)
        self.assertIn("RoundedCard(frame, fill=CARD)", source)
        self.assertIn("StepNumberChip", source)
        self.assertIn("fill=PURPLE", source)
        self.assertIn("background=CARD", source)
        self.assertIn('style="CardStrong.TLabel"', source)
        self.assertIn("background=BORDER, width=1", source)
        self.assertIn("text.PASTE_UIDS_INSTRUCTION", source)
        self.assertIn("text.DOWNLOAD_CSV_INSTRUCTION", source)
        self.assertIn("text.RETURN_CONTINUE_INSTRUCTION", source)
        self.assertIn("text.COPY_UIDS_BUTTON", source)
        self.assertIn("DANGER_BG if failed else SUCCESS_BG", source)
        self.assertIn("DangerCardHeading.TLabel", source)
        self.assertIn("text.NO_MISSING_UIDS_HEADING", source)
        self.assertIn("text.CLIPBOARD_FAILURE_HEADING", source)
        self.assertIn("text.LOST_UIDS_CAPTION", source)
        self.assertIn("text.COPY_BUTTON", source)
        self.assertIn("text.NO_CLIPBOARD_HANDOFF", source)
        self.assertNotIn("TABLEAU_HANDOFF_INTRO", source)

    def test_step_three_uses_one_recent_file_action_card(self) -> None:
        source = inspect.getsource(HostedPlayersReportApp.render_reactivated)

        self.assertIn("latest = latest_reengagement_csv()", source)
        self.assertEqual(source.count("RoundedCard("), 1)
        self.assertIn("RoundedCard(frame, fill=CARD, border=BORDER)", source)
        self.assertIn("latest.name", source)
        self.assertIn("text.recent_download_modified", source)
        self.assertIn("text.USE_RECENT_FILE_BUTTON", source)
        self.assertIn("self._choose_reactivated(latest)", source)
        self.assertIn("self._browse_reactivated", source)
        self.assertEqual(source.count('icon="folder"'), 2)
        self.assertIn("min_width=52", source)
        self.assertNotIn("BROWSE", source)
        self.assertIn("text.NO_RECENT_DOWNLOAD", source)
        self.assertIn("text.BACK_BUTTON", source)
        self.assertNotIn("LATEST_DOWNLOAD_CAPTION", source)
        self.assertNotIn("CHOOSE_ANOTHER_FILE_CAPTION", source)
        self.assertNotIn("other = RoundedCard", source)
        self.assertNotIn("SELECT_EXPORT_SUBTITLE", source)
        self.assertEqual(text.SELECT_EXPORT_HEADING, "Select Tableau export")
        self.assertEqual(text.USE_RECENT_FILE_BUTTON, "Select")

    def test_recent_download_copy_matches_the_single_card_metadata(self) -> None:
        modified = datetime(2026, 7, 15, 11, 19)
        with patch("hpr.gui.text.datetime") as datetime_type:
            datetime_type.fromtimestamp.return_value = modified
            datetime_type.now.return_value = modified

            result = text.recent_download_modified(0)

        self.assertEqual(result, "Downloads · today at 11:19 AM")

    def test_success_screen_uses_progress_gradient_and_neutral_detail_card(self) -> None:
        source = inspect.getsource(HostedPlayersReportApp.render_done)

        self.assertIn("GradientBanner", source)
        self.assertIn("text.SUCCESS_HEADING", source)
        self.assertIn("colors=(SUCCESS_BANNER_DARK, *GRADIENT)", source)
        self.assertIn("height=84", source)
        self.assertIn("text_color=TEAL", source)
        self.assertIn("RoundedCard(frame, fill=CARD)", source)
        self.assertIn('style="CardMuted.TLabel"', source)
        self.assertIn('style="Card.TLabel"', source)
        self.assertIn("background=BORDER, height=1", source)
        self.assertIn('anchor="e"', source)
        self.assertIn('justify="right"', source)
        self.assertNotIn("SUCCESS_BG", source)
        self.assertNotIn("SuccessCard", source)
        self.assertNotIn("REPORT_READY_SUBTITLE", source)
        self.assertIn("text.QA_TITLE", source)
        self.assertIn("text.OPEN_WORKBOOK_BUTTON", source)
        self.assertIn("self._start_over", source)
        self.assertIn('icon="back"', source)
        self.assertNotIn("START_OVER_BUTTON", source)
        self.assertNotIn("CLOSE_BUTTON", source)
        self.assertNotIn("self.destroy", source)
        self.assertIn("text.REACTIVATED_PLAYERS_LABEL", source)
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
        self.assertEqual(app.data.build_attempts, 0)
        self.assertFalse(app._file_chips_gradient)
        self.assertEqual(rendered, [True])


if __name__ == "__main__":
    unittest.main()
