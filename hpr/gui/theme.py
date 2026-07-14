"""Visual constants."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass
from tkinter import ttk

FontSpec = str | tkfont.Font | tuple[str, int] | tuple[str, int, str]

HEADER_BG = "#A7A9B4"
HEADER_TITLE = "#180A2E"
HEADER_STEP = "#180A2E"
STEP_ACTIVE = "#6A39BE"
STEP_IDLE = "#555565"

BG = "#1C1A31"
CARD = "#262340"
CARD_HOVER = "#2F2B4E"
SUNK = "#201D38"
BORDER = "#3A3556"
DIVIDER = "#2A2742"
PURPLE = "#7E46D8"
PURPLE_LIGHT = "#8A58D0"
PURPLE_PRESS = "#6A39BE"
BLUE = "#0093B8"
TEAL = "#00A892"
RED = "#FF6B7A"
TEXT = "#EDEEF0"
MUTED = "#A7A9B4"
WHITE = "#FFFFFF"
FOCUS = "#D6C4FF"

INFO_BG = "#1E2C45"
SUCCESS_BG = "#1D333B"
DANGER_BG = "#3D2036"

GRADIENT = [PURPLE, PURPLE_LIGHT, BLUE, TEAL]

# Prefer first installed font in each list.
HEADING_FONT_PREFS = [
    "Trade Gothic Next Cond",
    "Trade Gothic Next Condensed",
    "Trade Gothic Next",
    "Oswald",
    "Segoe UI Semibold",
    "Segoe UI",
    "Helvetica Neue",
    "Arial",
]
BODY_FONT_PREFS = ["Montserrat", "Segoe UI", "Helvetica Neue", "Arial"]


@dataclass(frozen=True, slots=True)
class GuiFonts:
    """Group app fonts."""

    title: FontSpec
    heading: FontSpec
    body: FontSpec
    body_bold: FontSpec
    small: FontSpec


def apply_styles(root: tk.Tk) -> GuiFonts:
    """Apply GUI theme and return fonts."""

    available = set(tkfont.families(root))
    heading = resolve_font_family(HEADING_FONT_PREFS, available)
    body = resolve_font_family(BODY_FONT_PREFS, available)
    fonts = GuiFonts(
        title=(heading, 22, "bold"),
        heading=(heading, 16, "bold"),
        body=(body, 11),
        body_bold=(body, 11, "bold"),
        small=(body, 10),
    )

    root.configure(background=BG)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", background=BG, foreground=TEXT, bordercolor=BORDER, font=fonts.body)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=TEXT, font=fonts.body)
    style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=fonts.body)
    style.configure("Small.TLabel", background=BG, foreground=MUTED, font=fonts.small)
    style.configure("Strong.TLabel", background=BG, foreground=TEXT, font=fonts.body_bold)
    style.configure("Heading.TLabel", background=BG, foreground=TEXT, font=fonts.heading)
    style.configure("Success.TLabel", background=BG, foreground=TEAL, font=fonts.heading)
    style.configure("Error.TLabel", background=BG, foreground=RED, font=fonts.heading)
    style.configure("Caption.TLabel", background=BG, foreground=MUTED, font=fonts.small)

    style.configure("SuccessCard.TLabel", background=SUCCESS_BG, foreground=TEXT, font=fonts.body)
    style.configure("SuccessCardMuted.TLabel", background=SUCCESS_BG, foreground=MUTED, font=fonts.body)
    style.configure("SuccessCardHeading.TLabel", background=SUCCESS_BG, foreground=TEXT, font=fonts.heading)
    style.configure("InfoCardMuted.TLabel", background=INFO_BG, foreground=MUTED, font=fonts.body)
    style.configure("InfoCardHeading.TLabel", background=INFO_BG, foreground=TEXT, font=fonts.heading)
    style.configure("DangerCardMuted.TLabel", background=DANGER_BG, foreground=MUTED, font=fonts.body)
    style.configure("DangerCardHeading.TLabel", background=DANGER_BG, foreground=TEXT, font=fonts.heading)

    style.configure("Header.TFrame", background=HEADER_BG)
    style.configure("Title.TLabel", background=HEADER_BG, foreground=HEADER_TITLE, font=fonts.title)
    style.configure("Divider.TFrame", background=DIVIDER)

    style.configure(
        "TEntry",
        fieldbackground=CARD,
        foreground=TEXT,
        bordercolor=BORDER,
        insertcolor=TEXT,
        padding=8,
    )
    style.map(
        "TEntry",
        fieldbackground=[("readonly", CARD)],
        foreground=[("readonly", TEXT)],
        bordercolor=[("focus", PURPLE)],
    )

    style.configure("TCheckbutton", background=BG, foreground=TEXT, focuscolor=BG, font=fonts.body)
    style.map(
        "TCheckbutton",
        background=[("active", BG)],
        indicatorcolor=[("selected", PURPLE), ("!selected", CARD)],
    )

    style.configure(
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
    style.map(
        "Link.TButton",
        background=[("active", BG), ("pressed", BG)],
        foreground=[("active", TEXT), ("pressed", TEXT)],
    )
    return fonts


def resolve_font_family(preferences: list[str], available: set[str]) -> str:
    """Return first installed preferred font."""

    lowered = {name.lower() for name in available}
    for family in preferences:
        if family.lower() in lowered:
            return family
    return preferences[-1]


def gradient_color_at(fraction: float, stops: list[str] | None = None) -> str:
    """Same gradient from 0 to 1."""

    stops = stops or GRADIENT
    if fraction <= 0:
        return stops[0]
    if fraction >= 1:
        return stops[-1]
    segments = len(stops) - 1
    scaled = fraction * segments
    index = int(scaled)
    return _blend(stops[index], stops[index + 1], scaled - index)


def round_points(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    r: float,
) -> list[float]:
    """Return points for rounded rectangle."""

    return [
        x1 + r,
        y1,
        x2 - r,
        y1,
        x2,
        y1,
        x2,
        y1 + r,
        x2,
        y2 - r,
        x2,
        y2,
        x2 - r,
        y2,
        x1 + r,
        y2,
        x1,
        y2,
        x1,
        y2 - r,
        x1,
        y1 + r,
        x1,
        y1,
    ]


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _blend(start: str, end: str, t: float) -> str:
    sr, sg, sb = _hex_to_rgb(start)
    er, eg, eb = _hex_to_rgb(end)
    r = round(sr + (er - sr) * t)
    g = round(sg + (eg - sg) * t)
    b = round(sb + (eb - sb) * t)
    return f"#{r:02x}{g:02x}{b:02x}"
