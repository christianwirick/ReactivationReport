from __future__ import annotations

import inspect
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch, sentinel

from hpr.gui import text
from hpr.gui.app import FILE_CHIP_SUCCESS_MS, HostedPlayersReportApp
from hpr.gui.screens import FILE_CHIP_GRADIENT_RANGES, FILE_CONNECTOR_GRADIENT_RANGE
from hpr.gui.state import GuiState
from hpr.gui.theme import STEP_IDLE, TEAL


class _FakeProgress:
    def __init__(self, *, animating: bool) -> None:
        self.animating = animating


class _FakeButton:
    def __init__(self) -> None:
        self.values: list[bool] = []

    def set_enabled(self, enabled: bool) -> None:
        self.values.append(enabled)


class _FakeBooleanVar:
    def __init__(self, value: bool) -> None:
        self.value = value

    def get(self) -> bool:
        return self.value


class _FakeStringVar:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def get(self) -> str:
        return self.value

    def set(self, value: str) -> None:
        self.value = value


class _FakeChip:
    def __init__(self) -> None:
        self.gradient_ranges: list[tuple[float, float]] = []
        self.solid_states: list[tuple[int | str, str]] = []

    def winfo_exists(self) -> bool:
        return True

    def set_vertical_gradient(self, start_fraction: float, end_fraction: float) -> None:
        self.gradient_ranges.append((start_fraction, end_fraction))

    def set_solid(self, number: int | str, fill: str) -> None:
        self.solid_states.append((number, fill))


class _FakeConnector:
    def __init__(self) -> None:
        self.gradient_ranges: list[tuple[float, float]] = []
        self.solid_fills: list[str] = []

    def winfo_exists(self) -> bool:
        return True

    def set_vertical_gradient(self, start_fraction: float, end_fraction: float) -> None:
        self.gradient_ranges.append((start_fraction, end_fraction))

    def set_solid(self, fill: str) -> None:
        self.solid_fills.append(fill)


class _FakeLabel:
    def __init__(self) -> None:
        self.text_updates: list[str] = []
        self.hidden = False

    def configure(self, *, text: str) -> None:
        self.text_updates.append(text)

    def grid_remove(self) -> None:
        self.hidden = True

    def grid(self) -> None:
        self.hidden = False


class GuiCloseTests(unittest.TestCase):
    def test_close_is_blocked_while_work_is_running(self) -> None:
        app = object.__new__(HostedPlayersReportApp)
        app.progress_controller = _FakeProgress(animating=True)

        with (
            patch("hpr.gui.app.messagebox.showinfo") as showinfo,
            patch.object(HostedPlayersReportApp, "destroy") as destroy,
        ):
            HostedPlayersReportApp._request_close(app)

        showinfo.assert_called_once_with(text.APP_TITLE, text.WORK_IN_PROGRESS, parent=app)
        destroy.assert_not_called()

    def test_close_proceeds_when_work_is_idle(self) -> None:
        app = object.__new__(HostedPlayersReportApp)
        app.progress_controller = _FakeProgress(animating=False)

        with patch.object(HostedPlayersReportApp, "destroy") as destroy:
            HostedPlayersReportApp._request_close(app)

        destroy.assert_called_once_with()

    def test_destroy_cancels_pending_file_chip_transition(self) -> None:
        source = inspect.getsource(HostedPlayersReportApp.destroy)

        self.assertIn("self._cancel_file_chip_transition()", source)


class HandoffControlTests(unittest.TestCase):
    def test_controls_track_handoff_enabled_state(self) -> None:
        app = object.__new__(HostedPlayersReportApp)
        primary = _FakeButton()
        browse = _FakeButton()
        settings = _FakeButton()
        app._primary_btn = primary
        app._handoff_buttons = [primary, browse, settings]

        HostedPlayersReportApp._set_handoff_controls(app, False)
        HostedPlayersReportApp._set_handoff_controls(app, True)

        self.assertEqual(primary.values, [False, True])
        self.assertEqual(browse.values, [False, True])
        self.assertEqual(settings.values, [False, True])


class ProgressCompletionTests(unittest.TestCase):
    def test_completed_progress_clears_status_and_discards_stale_stage_updates(self) -> None:
        app = object.__new__(HostedPlayersReportApp)
        app.progress_controller = Mock()
        app._stage_queue = sentinel.stage_queue
        completed: list[bool] = []

        HostedPlayersReportApp.finish_progress(app, lambda: completed.append(True))
        complete = app.progress_controller.finish.call_args.args[0]
        complete()

        app.progress_controller.set_busy.assert_called_once_with(False, "")
        self.assertIsNone(app._stage_queue)
        self.assertEqual(completed, [True])

    def test_stop_progress_discards_stale_stage_updates(self) -> None:
        app = object.__new__(HostedPlayersReportApp)
        app.progress_controller = Mock()
        app._stage_queue = sentinel.stage_queue

        HostedPlayersReportApp._stop_progress(app)

        self.assertIsNone(app._stage_queue)
        app.progress_controller.set_busy.assert_called_once_with(False, "")

    def test_handoff_error_stops_progress_before_showing_error(self) -> None:
        app = object.__new__(HostedPlayersReportApp)
        app._stop_progress = Mock()
        app._set_handoff_controls = Mock()
        app._show_error = Mock()
        app.data = GuiState()
        error = RuntimeError("handoff failed")

        HostedPlayersReportApp._handoff_error(app, error)

        app._stop_progress.assert_called_once_with()
        app._set_handoff_controls.assert_called_once_with(True)
        app._show_error.assert_called_once_with(error)

    def test_build_error_stops_progress_before_rendering_error(self) -> None:
        app = object.__new__(HostedPlayersReportApp)
        app._stop_progress = Mock()
        app.log = Mock()
        app.render_build = Mock()
        error = RuntimeError("build failed")

        HostedPlayersReportApp._build_error(app, error)

        app._stop_progress.assert_called_once_with()
        app.render_build.assert_called_once_with(str(error))


class StepOneOptionTests(unittest.TestCase):
    def test_step_one_replaces_pivot_option_with_unchecked_qa_option(self) -> None:
        settings_source = inspect.getsource(HostedPlayersReportApp.render_settings)
        init_source = inspect.getsource(HostedPlayersReportApp.__init__)

        self.assertIn("text=text.QA_OPTION", settings_source)
        self.assertEqual(text.QA_OPTION, "QA mode")
        self.assertNotIn("Create Pivot Tables", settings_source)
        self.assertIn("self.qa_var = tk.BooleanVar(value=False)", init_source)
        self.assertNotIn("native_pivot_var", init_source)

    def test_build_always_requests_native_pivots_and_forwards_qa(self) -> None:
        for qa_enabled in (False, True):
            with self.subTest(qa_enabled=qa_enabled):
                app = object.__new__(HostedPlayersReportApp)
                app.qa_var = _FakeBooleanVar(qa_enabled)
                app.data = GuiState(
                    hosted_path="hosted.csv",
                    lastweek_path="prior.xlsx",
                    market="Baton Rouge",
                    report_date=date(2026, 6, 1),
                    output_folder=Path("output"),
                    reactivated_csv=Path("reactivated.csv"),
                )
                app.theme_path = Path("theme.thmx")
                app.log = Mock()
                app._persist_settings = Mock()
                app.set_busy = Mock()
                app._progress_callback = Mock(return_value=sentinel.progress_callback)
                app.async_runner = Mock()

                HostedPlayersReportApp._start_build(app)
                work = app.async_runner.run.call_args.kwargs["work"]

                with patch("hpr.gui.app.run_report", return_value=sentinel.result) as run_report:
                    self.assertIs(work(), sentinel.result)

                run_report.assert_called_once_with(
                    hosted_csv_path="hosted.csv",
                    last_week_xlsx_path="prior.xlsx",
                    market="Baton Rouge",
                    report_date=date(2026, 6, 1),
                    output_folder=Path("output"),
                    theme_path=Path("theme.thmx"),
                    reactivated_csv_path=Path("reactivated.csv"),
                    overwrite=True,
                    create_native_pivot=True,
                    require_native_pivot=False,
                    include_copy_sheet=qa_enabled,
                    progress_callback=sentinel.progress_callback,
                )


class StepOneFileSelectionTests(unittest.TestCase):
    def test_hosted_selection_refreshes_the_state_aware_file_card(self) -> None:
        app = object.__new__(HostedPlayersReportApp)
        selected = Path("reports") / "Hosted Players.csv"
        app.hosted_var = _FakeStringVar()
        app.outdir_var = _FakeStringVar()
        app._settings = {"last_hosted_dir": ""}
        app._persist_settings = Mock()
        app._refresh_file_rows = Mock()
        app.render_inputs = Mock()

        with patch("hpr.gui.app.filedialog.askopenfilename", return_value=str(selected)):
            HostedPlayersReportApp._browse_hosted(app)

        self.assertEqual(app.hosted_var.get(), str(selected))
        self.assertEqual(app.outdir_var.get(), str(selected.parent / "outputs"))
        self.assertEqual(app._settings["last_hosted_dir"], str(selected.parent))
        app._persist_settings.assert_called_once_with()
        app._refresh_file_rows.assert_called_once_with()
        app.render_inputs.assert_not_called()

    def test_prior_workbook_selection_refreshes_the_state_aware_file_card(self) -> None:
        app = object.__new__(HostedPlayersReportApp)
        selected = Path("reports") / "Prior report.xlsx"
        app.lastweek_var = _FakeStringVar()
        app._settings = {"last_lastweek_dir": ""}
        app._persist_settings = Mock()
        app._refresh_file_rows = Mock()
        app.render_inputs = Mock()

        with patch("hpr.gui.app.filedialog.askopenfilename", return_value=str(selected)):
            HostedPlayersReportApp._browse_lastweek(app)

        self.assertEqual(app.lastweek_var.get(), str(selected))
        self.assertEqual(app._settings["last_lastweek_dir"], str(selected.parent))
        app._persist_settings.assert_called_once_with()
        app._refresh_file_rows.assert_called_once_with()
        app.render_inputs.assert_not_called()

    def test_refresh_file_rows_updates_partial_selection_without_rerendering(self) -> None:
        app = object.__new__(HostedPlayersReportApp)
        app.hosted_var = _FakeStringVar("reports/Hosted Players.csv")
        app.lastweek_var = _FakeStringVar()
        app._file_chips_gradient = True
        app._file_chips = [_FakeChip(), _FakeChip()]
        app._file_rows = [(_FakeLabel(), _FakeLabel()), (_FakeLabel(), _FakeLabel())]
        app._file_connector = _FakeConnector()
        app._schedule_file_chip_gradient = Mock()

        HostedPlayersReportApp._refresh_file_rows(app)

        self.assertFalse(app._file_chips_gradient)
        self.assertEqual(app._file_chips[0].solid_states, [("✓", TEAL)])
        self.assertEqual(app._file_chips[1].solid_states, [(2, STEP_IDLE)])
        self.assertEqual(app._file_rows[0][0].text_updates, ["Hosted Players.csv"])
        self.assertTrue(app._file_rows[0][1].hidden)
        self.assertEqual(app._file_rows[1][0].text_updates, [text.LAST_WEEK_WORKBOOK_LABEL])
        self.assertEqual(app._file_rows[1][1].text_updates, [text.LAST_WEEK_WORKBOOK_HINT])
        self.assertFalse(app._file_rows[1][1].hidden)
        self.assertEqual(app._file_connector.solid_fills, [TEAL])
        app._schedule_file_chip_gradient.assert_called_once_with()

    def test_refresh_file_rows_resets_both_chips_before_gradient(self) -> None:
        app = object.__new__(HostedPlayersReportApp)
        app.hosted_var = _FakeStringVar("hosted.csv")
        app.lastweek_var = _FakeStringVar("prior.xlsx")
        app._file_chips_gradient = True
        app._file_chips = [_FakeChip(), _FakeChip()]
        app._file_rows = [(_FakeLabel(), _FakeLabel()), (_FakeLabel(), _FakeLabel())]
        app._file_connector = _FakeConnector()
        app._schedule_file_chip_gradient = Mock()

        HostedPlayersReportApp._refresh_file_rows(app)

        self.assertFalse(app._file_chips_gradient)
        self.assertEqual([chip.solid_states for chip in app._file_chips], [[("✓", TEAL)], [("✓", TEAL)]])
        self.assertEqual(app._file_connector.solid_fills, [TEAL])
        app._schedule_file_chip_gradient.assert_called_once_with()

    def test_two_selected_files_schedule_a_brief_teal_state(self) -> None:
        app = object.__new__(HostedPlayersReportApp)
        app.hosted_var = _FakeStringVar("hosted.csv")
        app.lastweek_var = _FakeStringVar("prior.xlsx")
        app._file_chips_gradient = False
        app._file_chip_transition_after = None
        app.after = Mock(return_value="transition-id")
        app.after_cancel = Mock()

        HostedPlayersReportApp._schedule_file_chip_gradient(app)

        app.after.assert_called_once_with(FILE_CHIP_SUCCESS_MS, app._apply_file_chip_gradient)
        self.assertEqual(app._file_chip_transition_after, "transition-id")

    def test_completed_file_transition_applies_the_progress_gradient(self) -> None:
        app = object.__new__(HostedPlayersReportApp)
        app.hosted_var = _FakeStringVar("hosted.csv")
        app.lastweek_var = _FakeStringVar("prior.xlsx")
        app._file_chips_gradient = False
        app._file_chip_transition_after = "transition-id"
        chips = [_FakeChip(), _FakeChip()]
        app._file_chips = chips
        connector = _FakeConnector()
        app._file_connector = connector

        HostedPlayersReportApp._apply_file_chip_gradient(app)

        self.assertTrue(app._file_chips_gradient)
        self.assertIsNone(app._file_chip_transition_after)
        self.assertEqual(
            [chip.gradient_ranges for chip in chips], [[FILE_CHIP_GRADIENT_RANGES[0]], [FILE_CHIP_GRADIENT_RANGES[1]]]
        )
        self.assertEqual(connector.gradient_ranges, [FILE_CONNECTOR_GRADIENT_RANGE])

    def test_pending_file_transition_can_be_cancelled(self) -> None:
        app = object.__new__(HostedPlayersReportApp)
        app._file_chip_transition_after = "transition-id"
        app.after_cancel = Mock()

        HostedPlayersReportApp._cancel_file_chip_transition(app)

        app.after_cancel.assert_called_once_with("transition-id")
        self.assertIsNone(app._file_chip_transition_after)


if __name__ == "__main__":
    unittest.main()
