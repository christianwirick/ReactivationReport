from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from hpr.gui.theme import BG, HEADER_BG, HEADER_TITLE, MUTED, PURPLE_LIGHT, apply_styles


class GuiThemeTests(unittest.TestCase):
    def test_styles_use_available_preferred_fonts(self) -> None:
        root = MagicMock()
        style = MagicMock()
        with (
            patch("hpr.gui.theme.tkfont.families", return_value=("Segoe UI", "Arial")),
            patch("hpr.gui.theme.ttk.Style", return_value=style),
        ):
            fonts = apply_styles(root)

        self.assertEqual(fonts.title, ("Segoe UI", 22, "bold"))
        self.assertEqual(fonts.body, ("Segoe UI", 11))
        root.configure.assert_called_once_with(background=BG)
        style.theme_use.assert_called_once_with("clam")
        style.configure.assert_any_call(
            "Title.TLabel",
            background=HEADER_BG,
            foreground=HEADER_TITLE,
            font=fonts.title,
        )
        style.configure.assert_any_call(
            "Link.TButton",
            background=BG,
            foreground=MUTED,
            bordercolor=BG,
            focuscolor=PURPLE_LIGHT,
            borderwidth=0,
            relief="flat",
            font=fonts.body_bold,
            padding=(0, 6),
        )


if __name__ == "__main__":
    unittest.main()
