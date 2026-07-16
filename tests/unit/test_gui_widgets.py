from __future__ import annotations

import inspect
import tkinter as tk
import unittest

from hpr.gui.theme import HEADER_BG, PURPLE
from hpr.gui.widgets import (
    GradientBanner,
    GradientConnector,
    RoundedButton,
    RoundedEntry,
    RoundedProgressBar,
    StepNumberChip,
    Stepper,
    _rounded_shape_rows,
    scroll_needed,
    step_marks,
)


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


class AntialiasedStepGraphicsTests(unittest.TestCase):
    def test_rounded_shape_blends_edge_pixels_against_its_background(self) -> None:
        rows = _rounded_shape_rows(8, 8, PURPLE, HEADER_BG)
        colors = {color for row in rows for color in row}

        self.assertEqual(rows[0][0], HEADER_BG.lower())
        self.assertEqual(rows[3][3], PURPLE.lower())
        self.assertGreater(len(colors), 2)

    def test_stepper_uses_antialiased_images_instead_of_canvas_primitives(self) -> None:
        source = inspect.getsource(Stepper._draw)

        self.assertIn("_rounded_shape_image", source)
        self.assertNotIn("create_line", source)
        self.assertNotIn("create_oval", source)

    def test_number_chip_uses_a_sharp_tk_label_over_an_antialiased_image(self) -> None:
        source = inspect.getsource(StepNumberChip)

        self.assertTrue(issubclass(StepNumberChip, tk.Label))
        self.assertIn("_rounded_shape_image", source)
        self.assertIn('compound="center"', source)
        self.assertIn("number: int | str", source)
        self.assertNotIn("create_oval", source)

    def test_number_chip_can_adopt_a_vertical_progress_gradient_segment(self) -> None:
        source = inspect.getsource(StepNumberChip.set_vertical_gradient)

        self.assertIn("_rounded_shape_image", source)
        self.assertIn("gradient_color_at", source)
        self.assertIn("start_fraction", source)
        self.assertIn("end_fraction", source)
        self.assertIn("self.configure(image=self._image)", source)

    def test_number_chip_can_update_solid_state_without_replacement(self) -> None:
        source = inspect.getsource(StepNumberChip.set_solid)

        self.assertIn("_rounded_shape_image", source)
        self.assertIn("text=str(number)", source)
        self.assertIn("self.configure", source)

    def test_gradient_banner_reuses_antialiasing_and_progress_color_math(self) -> None:
        source = inspect.getsource(GradientBanner)

        self.assertTrue(issubclass(GradientBanner, tk.Canvas))
        self.assertIn("colors or GRADIENT", source)
        self.assertIn("_rounded_shape_image", source)
        self.assertIn("samples=2", source)
        self.assertIn("gradient_color_at", source)
        self.assertIn("self.create_text(", source)
        self.assertTrue(hasattr(RoundedProgressBar, "_cap_inset"))

    def test_file_connector_draws_its_vertical_gradient_segment(self) -> None:
        source = inspect.getsource(GradientConnector.set_vertical_gradient)

        self.assertTrue(issubclass(GradientConnector, tk.Canvas))
        self.assertIn("for y in range(self._height)", source)
        self.assertIn("gradient_color_at(fraction)", source)

    def test_file_connector_can_update_solid_state_without_replacement(self) -> None:
        source = inspect.getsource(GradientConnector.set_solid)

        self.assertIn('self.delete("all")', source)
        self.assertIn("self.create_rectangle", source)


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


class RoundedControlSourceTests(unittest.TestCase):
    def test_folder_button_uses_a_vector_icon(self) -> None:
        source = inspect.getsource(RoundedButton)

        self.assertIn('self._icon == "folder"', source)
        self.assertIn("_draw_folder_icon", source)
        self.assertIn("min_height", source)
        self.assertNotIn("📁", source)

    def test_settings_icons_are_vector_drawn(self) -> None:
        source = inspect.getsource(RoundedButton)

        self.assertIn('self._icon == "gear"', source)
        self.assertIn("_draw_gear_icon", source)
        self.assertIn("self.create_polygon(points", source)
        self.assertIn("fill=background", source)
        self.assertIn('self._icon == "close"', source)
        self.assertIn("_draw_close_icon", source)
        self.assertNotIn("⚙", source)

    def test_done_back_control_uses_a_vector_icon(self) -> None:
        source = inspect.getsource(RoundedButton)

        self.assertIn('self._icon == "back"', source)
        self.assertIn("_draw_back_icon", source)
        self.assertIn("capstyle=tk.ROUND", inspect.getsource(RoundedButton._draw_back_icon))

    def test_rounded_entry_uses_card_fill_and_a_flat_inner_entry(self) -> None:
        source = inspect.getsource(RoundedEntry)

        self.assertIn("radius=14", source)
        self.assertIn("fill: str = CARD", source)
        self.assertIn("fill=fill", source)
        self.assertIn("self.configure(height=48)", source)
        self.assertIn('relief="flat"', source)
        self.assertIn('state="readonly" if readonly else "normal"', source)


if __name__ == "__main__":
    unittest.main()
