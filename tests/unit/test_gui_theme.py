from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from hpr.gui.theme import (
    BG,
    CARD,
    HEADER_BG,
    HEADER_TITLE,
    MUTED,
    SETTINGS_BG,
    SETTINGS_CARD,
    SUCCESS_BANNER_DARK,
    TEXT,
    apply_styles,
)


class GuiThemeTests(unittest.TestCase):
    def test_success_banner_starts_darker_than_the_page(self) -> None:
        def channel_sum(color: str) -> int:
            return sum(int(color[index : index + 2], 16) for index in (1, 3, 5))

        self.assertLess(channel_sum(SUCCESS_BANNER_DARK), channel_sum(BG))

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
        style.configure.assert_any_call("Card.TLabel", background=CARD, foreground=TEXT, font=fonts.body)
        style.configure.assert_any_call("Card.TFrame", background=CARD)
        style.configure.assert_any_call(
            "CardHeading.TLabel",
            background=CARD,
            foreground=TEXT,
            font=fonts.heading,
        )
        style.configure.assert_any_call(
            "CardStrong.TLabel",
            background=CARD,
            foreground=TEXT,
            font=fonts.body_bold,
        )
        style.configure.assert_any_call("CardMuted.TLabel", background=CARD, foreground=MUTED, font=fonts.body)
        style.configure.assert_any_call("Settings.TFrame", background=SETTINGS_BG)
        style.configure.assert_any_call(
            "SettingsSmall.TLabel",
            background=SETTINGS_BG,
            foreground=MUTED,
            font=fonts.small,
        )
        style.configure.assert_any_call(
            "SettingsHeading.TLabel",
            background=SETTINGS_BG,
            foreground=TEXT,
            font=fonts.heading,
        )
        style.configure.assert_any_call(
            "SettingsCard.TLabel",
            background=SETTINGS_CARD,
            foreground=TEXT,
            font=fonts.body,
        )


if __name__ == "__main__":
    unittest.main()
