from __future__ import annotations

import unittest
from unittest.mock import patch

from hpr.gui import text
from hpr.gui.app import HostedPlayersReportApp


class _FakeProgress:
    def __init__(self, *, animating: bool) -> None:
        self.animating = animating


class _FakeButton:
    def __init__(self) -> None:
        self.values: list[bool] = []

    def set_enabled(self, enabled: bool) -> None:
        self.values.append(enabled)


class _FakeToggle:
    def __init__(self) -> None:
        self.values: list[list[str]] = []

    def state(self, values: list[str]) -> None:
        self.values.append(values)


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


class HandoffControlTests(unittest.TestCase):
    def test_controls_track_handoff_enabled_state(self) -> None:
        app = object.__new__(HostedPlayersReportApp)
        primary = _FakeButton()
        browse = _FakeButton()
        toggle = _FakeToggle()
        app._primary_btn = primary
        app._handoff_buttons = [primary, browse]
        app._options_toggle = toggle

        HostedPlayersReportApp._set_handoff_controls(app, False)
        HostedPlayersReportApp._set_handoff_controls(app, True)

        self.assertEqual(primary.values, [False, True])
        self.assertEqual(browse.values, [False, True])
        self.assertEqual(toggle.values, [["disabled"], ["!disabled"]])


if __name__ == "__main__":
    unittest.main()
