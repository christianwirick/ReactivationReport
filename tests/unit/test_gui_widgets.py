from __future__ import annotations

import unittest

from hpr.gui.screens import Screens
from hpr.gui.widgets import RoundedButton, scroll_needed, step_marks


class StepMarksTests(unittest.TestCase):
    def test_marks_distinguish_done_current_and_future_steps(self) -> None:
        self.assertEqual(step_marks(2, 4), ("done", "current", "future", "future"))

    def test_marks_reject_invalid_positions(self) -> None:
        for step, total in ((0, 4), (5, 4), (1, 0)):
            with self.subTest(step=step, total=total), self.assertRaises(ValueError):
                step_marks(step, total)


class ScrollVisibilityTests(unittest.TestCase):
    def test_scrollbar_is_only_needed_for_overflow(self) -> None:
        self.assertFalse(scroll_needed(None, 100))
        self.assertFalse(scroll_needed((0, 0, 100, 100), 100))
        self.assertTrue(scroll_needed((0, 10, 100, 111), 100))


class RoundedButtonKeyboardTests(unittest.TestCase):
    def test_keyboard_activation_runs_enabled_command_and_stops_propagation(self) -> None:
        calls: list[bool] = []
        button = object.__new__(RoundedButton)
        button._enabled = True
        button._command = lambda: calls.append(True)

        result = RoundedButton._on_key(button, None)

        self.assertEqual(calls, [True])
        self.assertEqual(result, "break")

    def test_keyboard_activation_ignores_disabled_button(self) -> None:
        calls: list[bool] = []
        button = object.__new__(RoundedButton)
        button._enabled = False
        button._command = lambda: calls.append(True)

        result = RoundedButton._on_key(button, None)

        self.assertEqual(calls, [])
        self.assertEqual(result, "break")


class OptionsKeyboardTests(unittest.TestCase):
    def test_return_toggles_options_and_stops_primary_action(self) -> None:
        calls: list[bool] = []
        screens = object.__new__(Screens)
        screens._toggle_options = lambda: calls.append(True)

        result = Screens._toggle_options_key(screens, None)

        self.assertEqual(calls, [True])
        self.assertEqual(result, "break")


if __name__ == "__main__":
    unittest.main()
