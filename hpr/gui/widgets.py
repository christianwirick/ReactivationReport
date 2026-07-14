"""Custom canvas widgets."""

from __future__ import annotations

import math
import tkinter as tk
from collections.abc import Callable
from typing import Literal

from .theme import (
    BG,
    BORDER,
    FOCUS,
    HEADER_BG,
    HEADER_STEP,
    MUTED,
    STEP_ACTIVE,
    STEP_IDLE,
    FontSpec,
    gradient_color_at,
    round_points,
)

StepMark = Literal["done", "current", "future"]


def scroll_needed(bounds: tuple[int, int, int, int] | None, viewport_height: int) -> bool:
    """Return whether content exceeds vertical viewport."""

    return bounds is not None and bounds[3] - bounds[1] > max(0, viewport_height)


def step_marks(step: int, total: int) -> tuple[StepMark, ...]:
    """Return visual state of each wizard step."""

    if total < 1:
        raise ValueError("total must be positive")
    if not 1 <= step <= total:
        raise ValueError("step must be within the wizard")

    marks: list[StepMark] = []
    for number in range(1, total + 1):
        if number < step:
            marks.append("done")
        elif number == step:
            marks.append("current")
        else:
            marks.append("future")
    return tuple(marks)


class Stepper(tk.Canvas):
    """Display current wizard step."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        font: FontSpec,
        total: int = 4,
        width: int = 190,
        height: int = 22,
    ) -> None:
        super().__init__(
            master,
            width=width,
            height=height,
            bg=HEADER_BG,
            highlightthickness=0,
            bd=0,
            takefocus=0,
        )
        self._font = font
        self._total = total
        self._step = 1
        self._draw()

    def set_step(self, step: int) -> None:
        """Show current wizard step."""

        step_marks(step, self._total)
        self._step = step
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        label = self.create_text(
            0,
            11,
            anchor="w",
            text=f"Step {self._step} of {self._total}",
            fill=HEADER_STEP,
            font=self._font,
        )
        bounds = self.bbox(label)
        x = float(bounds[2] if bounds is not None else 72) + 14
        for mark in step_marks(self._step, self._total):
            color = STEP_ACTIVE if mark != "future" else STEP_IDLE
            if mark == "current":
                self.create_line(x, 11, x + 20, 11, fill=color, width=8, capstyle=tk.ROUND)
                x += 32
                continue
            self.create_oval(x, 7, x + 8, 15, fill=color, outline=color)
            x += 18


class RoundedProgressBar(tk.Canvas):
    """Display progress with a rounded gradient bar."""

    def __init__(self, master: tk.Misc, width: int = 260, height: int = 12) -> None:
        super().__init__(master, width=width, height=height, highlightthickness=0, bd=0, bg=BG)
        self._width = width
        self._height = height
        self._value = 0.0
        self._fill_items: list[int] = []
        self._visible_fill_width = -1
        self.bind("<Configure>", lambda _event: self._rebuild())

    def set_value(self, percent: float) -> None:
        """Set progress from 0 to 100."""

        self._value = max(0.0, min(100.0, float(percent)))
        self._apply_fill_width()

    @staticmethod
    def _cap_inset(x: float, width: float, radius: float, round_right: bool) -> float:
        """Calculate the inset for a rounded edge."""

        if x < radius:
            d = radius - 0.5 - x
        elif round_right and x > width - radius:
            d = x - (width - radius) + 0.5
        else:
            return 0.0
        return radius - math.sqrt(max(0.0, radius * radius - d * d))

    def _rebuild(self) -> None:
        """Redraw bar after resizing."""

        try:
            self.delete("all")
            width = self.winfo_width() or self._width
            height = self.winfo_height() or self._height
            radius = height / 2.0
            for x in range(width):
                inset = self._cap_inset(x, width, radius, True)
                self.create_line(x, inset, x, height - inset, fill=BORDER)
            self._fill_items = []
            for x in range(width):
                inset = self._cap_inset(x, width, radius, True)
                item = self.create_line(
                    x,
                    inset,
                    x,
                    height - inset,
                    fill=gradient_color_at(x / max(1, width - 1)),
                    state="hidden",
                )
                self._fill_items.append(item)
            self._visible_fill_width = -1
            self._apply_fill_width()
        except tk.TclError:
            pass

    def _apply_fill_width(self) -> None:
        try:
            if not self._fill_items:
                self._rebuild()
                return
            width = len(self._fill_items)
            fill_width = round(width * self._value / 100.0)
            fill_width = max(0, min(width, fill_width))
            if fill_width == self._visible_fill_width:
                return
            if fill_width > self._visible_fill_width:
                start = max(0, self._visible_fill_width)
                for item in self._fill_items[start:fill_width]:
                    self.itemconfigure(item, state="normal")
            else:
                for item in self._fill_items[fill_width : self._visible_fill_width]:
                    self.itemconfigure(item, state="hidden")
            self._visible_fill_width = fill_width
        except tk.TclError:
            pass


class RoundedButton(tk.Canvas):
    """Canvas button with rounded interactive states."""

    def __init__(
        self,
        master: tk.Misc,
        text: str,
        command: Callable[[], None] | None = None,
        *,
        parent_bg: str,
        fill: str,
        fill_hover: str,
        fill_press: str,
        text_color: str,
        font: FontSpec,
        radius: int = 13,
        pad_x: int = 20,
        pad_y: int = 11,
        min_width: int = 0,
        disabled_fill: str = BORDER,
        disabled_text: str = MUTED,
    ) -> None:
        super().__init__(master, highlightthickness=0, bd=0, bg=parent_bg, takefocus=1)
        self._command = command
        self._fill, self._hover, self._press = fill, fill_hover, fill_press
        self._text_color = text_color
        self._disabled_fill, self._disabled_text = disabled_fill, disabled_text
        self._radius, self._font, self._text = radius, font, text
        self._enabled = True
        self._focused = False

        probe = self.create_text(0, 0, text=text, font=font, anchor="nw")
        x1, y1, x2, y2 = self.bbox(probe)
        self.delete(probe)
        self._bw = max(min_width, (x2 - x1) + 2 * pad_x)
        self._bh = (y2 - y1) + 2 * pad_y + 2
        self.configure(width=self._bw, height=self._bh, cursor="hand2")

        self.bind("<Enter>", lambda _e: self._render(self._hover) if self._enabled else None)
        self.bind("<Leave>", lambda _e: self._render(self._fill) if self._enabled else None)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Return>", self._on_key)
        self.bind("<KP_Enter>", self._on_key)
        self.bind("<space>", self._on_key)
        self._render(self._fill)

    def _render(self, fill: str) -> None:
        self.delete("all")
        color = fill if self._enabled else self._disabled_fill
        text_color = self._text_color if self._enabled else self._disabled_text
        self.create_polygon(
            round_points(1, 1, self._bw - 1, self._bh - 1, self._radius),
            smooth=True,
            fill=color,
            outline=FOCUS if self._focused else color,
            width=2 if self._focused else 1,
        )
        self.create_text(self._bw / 2, self._bh / 2, text=self._text, fill=text_color, font=self._font)

    def _on_press(self, _event: tk.Event[tk.Canvas]) -> None:
        if not self._enabled:
            return
        self.focus_set()
        self._render(self._press)

    def _on_release(self, event: tk.Event[tk.Canvas]) -> None:
        if not self._enabled:
            return
        inside = 0 <= event.x <= self._bw and 0 <= event.y <= self._bh
        self._render(self._hover if inside else self._fill)
        if inside and self._command:
            self._command()

    def _on_focus_in(self, _event: tk.Event[tk.Canvas]) -> None:
        self._focused = True
        self._render(self._fill)

    def _on_focus_out(self, _event: tk.Event[tk.Canvas]) -> None:
        self._focused = False
        self._render(self._fill)

    def _on_key(self, _event: tk.Event[tk.Canvas] | None) -> str:
        if self._enabled and self._command is not None:
            self._command()
        return "break"

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the button."""

        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow", takefocus=1 if enabled else 0)
        self._render(self._fill)


class RoundedCard(tk.Frame):
    """Frame with a rounded border and optional accent."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        radius: int = 16,
        fill: str = BG,
        border: str = BORDER,
        accent: str | None = None,
    ) -> None:
        super().__init__(master, bg=fill)
        self._radius = radius
        self._fill = fill
        self._border = border
        self._accent = accent
        self._canvas = tk.Canvas(self, bg=BG, highlightthickness=0, bd=0)
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.tk.call("lower", self._canvas)
        self._canvas.bind("<Configure>", lambda _e: self._redraw())

    def _redraw(self) -> None:
        canvas = self._canvas
        try:
            canvas.delete("all")
            width, height = canvas.winfo_width(), canvas.winfo_height()
            if width < 4 or height < 4:
                return
            canvas.create_polygon(
                round_points(1, 1, width - 1, height - 1, self._radius),
                smooth=True,
                fill=self._fill,
                outline=self._border,
                width=1,
            )
            if self._accent is not None:
                canvas.create_line(
                    self._radius,
                    3,
                    width - self._radius,
                    3,
                    fill=self._accent,
                    width=5,
                    capstyle=tk.ROUND,
                )
        except tk.TclError:
            pass
