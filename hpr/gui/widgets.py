"""Custom canvas widgets."""

from __future__ import annotations

import math
import tkinter as tk
from collections.abc import Callable, Sequence
from typing import Literal

from . import text
from .theme import (
    BG,
    BORDER,
    CARD,
    FOCUS,
    GRADIENT,
    HEADER_BG,
    HEADER_STEP,
    MUTED,
    PURPLE,
    STEP_ACTIVE,
    STEP_IDLE,
    TEXT,
    WHITE,
    FontSpec,
    gradient_color_at,
    round_points,
)

StepMark = Literal["done", "current", "future"]
ButtonIcon = Literal["back", "close", "folder", "gear"]


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _blend_coverage(fill: str, background: str, coverage: float) -> str:
    fr, fg, fb = _hex_to_rgb(fill)
    br, bg, bb = _hex_to_rgb(background)
    red = round(br + (fr - br) * coverage)
    green = round(bg + (fg - bg) * coverage)
    blue = round(bb + (fb - bb) * coverage)
    return f"#{red:02x}{green:02x}{blue:02x}"


def _rounded_shape_rows(
    width: int,
    height: int,
    fill: str | Callable[[float, float], str],
    background: str,
    *,
    samples: int = 4,
    radius: float | None = None,
) -> tuple[tuple[str, ...], ...]:
    """Return antialiased pixels for a rounded shape."""

    shape_radius = min(radius if radius is not None else height / 2.0, width / 2.0, height / 2.0)
    sample_count = samples * samples
    rows: list[tuple[str, ...]] = []
    for pixel_y in range(height):
        row: list[str] = []
        for pixel_x in range(width):
            inside = 0
            for sample_y in range(samples):
                y = pixel_y + (sample_y + 0.5) / samples
                for sample_x in range(samples):
                    x = pixel_x + (sample_x + 0.5) / samples
                    nearest_x = min(max(x, shape_radius), width - shape_radius)
                    nearest_y = min(max(y, shape_radius), height - shape_radius)
                    if (x - nearest_x) ** 2 + (y - nearest_y) ** 2 <= shape_radius**2:
                        inside += 1
            fill_color = fill(pixel_x / max(1, width - 1), pixel_y / max(1, height - 1)) if callable(fill) else fill
            row.append(_blend_coverage(fill_color, background, inside / sample_count))
        rows.append(tuple(row))
    return tuple(rows)


def _rounded_shape_image(
    master: tk.Misc,
    width: int,
    height: int,
    fill: str | Callable[[float, float], str],
    background: str,
    *,
    samples: int = 4,
    radius: float | None = None,
) -> tk.PhotoImage:
    """Create a Tk image with antialiased rounded edges."""

    image = tk.PhotoImage(master=master, width=width, height=height)
    for y, row in enumerate(_rounded_shape_rows(width, height, fill, background, samples=samples, radius=radius)):
        image.put("{" + " ".join(row) + "}", to=(0, y))
    return image


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
        self._mark_images: list[tk.PhotoImage] = []
        self._draw()

    def set_step(self, step: int) -> None:
        """Show current wizard step."""

        step_marks(step, self._total)
        self._step = step
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        self._mark_images.clear()
        label = self.create_text(
            0,
            11,
            anchor="w",
            text=text.step_label(self._step, self._total),
            fill=HEADER_STEP,
            font=self._font,
        )
        bounds = self.bbox(label)
        x = float(bounds[2] if bounds is not None else 72) + 14
        for mark in step_marks(self._step, self._total):
            color = STEP_ACTIVE if mark != "future" else STEP_IDLE
            if mark == "current":
                image = _rounded_shape_image(self, 28, 8, color, HEADER_BG)
                self._mark_images.append(image)
                self.create_image(x, 7, anchor="nw", image=image)
                x += 32
                continue
            image = _rounded_shape_image(self, 8, 8, color, HEADER_BG)
            self._mark_images.append(image)
            self.create_image(x, 7, anchor="nw", image=image)
            x += 18


class StepNumberChip(tk.Label):
    """Display a numbered instruction chip."""

    def __init__(
        self,
        master: tk.Misc,
        number: int | str,
        *,
        font: FontSpec,
        fill: str,
        background: str,
        diameter: int = 32,
    ) -> None:
        self._diameter = diameter
        self._background = background
        self._image = _rounded_shape_image(master, diameter, diameter, fill, background)
        super().__init__(
            master,
            image=self._image,
            text=str(number),
            compound="center",
            width=diameter,
            height=diameter,
            bg=background,
            fg=TEXT,
            font=font,
            highlightthickness=0,
            bd=0,
            takefocus=0,
            padx=0,
            pady=0,
        )

    def set_solid(self, number: int | str, fill: str) -> None:
        """Update the chip text and solid fill without replacing the widget."""

        self._image = _rounded_shape_image(
            self,
            self._diameter,
            self._diameter,
            fill,
            self._background,
        )
        self.configure(image=self._image, text=str(number))

    def set_vertical_gradient(self, start_fraction: float, end_fraction: float) -> None:
        """Use a vertical segment of the progress-bar gradient."""

        self._image = _rounded_shape_image(
            self,
            self._diameter,
            self._diameter,
            lambda _x, y: gradient_color_at(start_fraction + (end_fraction - start_fraction) * y),
            self._background,
        )
        self.configure(image=self._image)


class GradientConnector(tk.Canvas):
    """Connect file chips with a solid or vertical gradient line."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        fill: str,
        background: str,
        width: int = 4,
        height: int = 18,
    ) -> None:
        super().__init__(
            master,
            width=width,
            height=height,
            bg=background,
            highlightthickness=0,
            bd=0,
            takefocus=0,
        )
        self._width = width
        self._height = height
        self.set_solid(fill)

    def set_solid(self, fill: str) -> None:
        """Update the connector fill without replacing the widget."""

        self.delete("all")
        self.create_rectangle(0, 0, self._width, self._height, fill=fill, outline=fill)

    def set_vertical_gradient(self, start_fraction: float, end_fraction: float) -> None:
        """Draw the connector's segment of the progress-bar gradient."""

        self.delete("all")
        for y in range(self._height):
            fraction = start_fraction + (end_fraction - start_fraction) * y / max(1, self._height - 1)
            self.create_line(0, y, self._width, y, fill=gradient_color_at(fraction))


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


class GradientBanner(tk.Canvas):
    """Display a rounded gradient success banner."""

    def __init__(
        self,
        master: tk.Misc,
        text: str,
        *,
        font: FontSpec,
        colors: Sequence[str] | None = None,
        height: int = 72,
        radius: int = 16,
        background: str = BG,
        text_color: str = WHITE,
    ) -> None:
        super().__init__(
            master,
            width=640,
            height=height,
            bg=background,
            highlightthickness=0,
            bd=0,
            takefocus=0,
        )
        self._text = text
        self._font = font
        self._colors = list(colors or GRADIENT)
        self._radius = radius
        self._background = background
        self._text_color = text_color
        self._image: tk.PhotoImage | None = None
        self._image_size: tuple[int, int] | None = None
        self.bind("<Configure>", self._draw)

    def _draw(self, _event: tk.Event[tk.Canvas] | None = None) -> None:
        self.delete("all")
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        if self._image is None or self._image_size != (width, height):
            self._image = _rounded_shape_image(
                self,
                width,
                height,
                lambda x, _y: gradient_color_at(x, self._colors),
                self._background,
                samples=2,
                radius=float(self._radius),
            )
            self._image_size = (width, height)
        self.create_image(0, 0, anchor="nw", image=self._image)
        self.create_text(
            20,
            height / 2,
            anchor="w",
            text=self._text,
            fill=self._text_color,
            font=self._font,
        )


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
        min_height: int = 0,
        border_color: str | None = None,
        icon: ButtonIcon | None = None,
        disabled_fill: str = BORDER,
        disabled_text: str = MUTED,
    ) -> None:
        super().__init__(master, highlightthickness=0, bd=0, bg=parent_bg, takefocus=1)
        self._command = command
        self._fill, self._hover, self._press = fill, fill_hover, fill_press
        self._text_color = text_color
        self._border_color = border_color
        self._icon = icon
        self._disabled_fill, self._disabled_text = disabled_fill, disabled_text
        self._radius, self._font, self._text = radius, font, text
        self._enabled = True
        self._focused = False

        if icon is None:
            probe = self.create_text(0, 0, text=text, font=font, anchor="nw")
            bounds = self.bbox(probe)
            self.delete(probe)
            text_width = bounds[2] - bounds[0] if bounds is not None else 0
            text_height = bounds[3] - bounds[1] if bounds is not None else 16
        else:
            text_width, text_height = (24, 18) if icon == "folder" else (22, 22)
        self._bw = max(min_width, text_width + 2 * pad_x)
        self._bh = max(min_height, text_height + 2 * pad_y + 2)
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
            outline=FOCUS if self._focused else self._border_color or color,
            width=2 if self._focused else 1,
        )
        if self._icon == "folder":
            self._draw_folder_icon(text_color)
        elif self._icon == "gear":
            self._draw_gear_icon(text_color, color)
        elif self._icon == "close":
            self._draw_close_icon(text_color)
        elif self._icon == "back":
            self._draw_back_icon(text_color)
        else:
            self.create_text(self._bw / 2, self._bh / 2, text=self._text, fill=text_color, font=self._font)

    def _draw_folder_icon(self, color: str) -> None:
        center_x, center_y = self._bw / 2, self._bh / 2
        self.create_polygon(
            center_x - 12,
            center_y - 7,
            center_x - 4,
            center_y - 7,
            center_x,
            center_y - 3,
            center_x + 12,
            center_y - 3,
            center_x + 12,
            center_y + 8,
            center_x - 12,
            center_y + 8,
            fill="",
            outline=color,
            width=2,
            joinstyle=tk.ROUND,
        )

    def _draw_gear_icon(self, color: str, background: str) -> None:
        center_x, center_y = self._bw / 2, self._bh / 2
        points: list[float] = []
        for index in range(32):
            radius = 11 if index % 4 in (1, 2) else 8
            angle = -math.pi / 2 + math.tau * index / 32
            points.extend((center_x + math.cos(angle) * radius, center_y + math.sin(angle) * radius))
        self.create_polygon(points, fill=color, outline=color)
        self.create_oval(
            center_x - 4,
            center_y - 4,
            center_x + 4,
            center_y + 4,
            fill=background,
            outline=background,
        )

    def _draw_close_icon(self, color: str) -> None:
        center_x, center_y = self._bw / 2, self._bh / 2
        self.create_line(
            center_x - 7,
            center_y - 7,
            center_x + 7,
            center_y + 7,
            fill=color,
            width=2,
            capstyle=tk.ROUND,
        )
        self.create_line(
            center_x + 7,
            center_y - 7,
            center_x - 7,
            center_y + 7,
            fill=color,
            width=2,
            capstyle=tk.ROUND,
        )

    def _draw_back_icon(self, color: str) -> None:
        center_x, center_y = self._bw / 2, self._bh / 2
        self.create_line(
            center_x - 8,
            center_y,
            center_x + 8,
            center_y,
            fill=color,
            width=2,
            capstyle=tk.ROUND,
        )
        self.create_line(
            center_x - 8,
            center_y,
            center_x - 1,
            center_y - 7,
            fill=color,
            width=2,
            capstyle=tk.ROUND,
        )
        self.create_line(
            center_x - 8,
            center_y,
            center_x - 1,
            center_y + 7,
            fill=color,
            width=2,
            capstyle=tk.ROUND,
        )

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
        parent_bg: str = BG,
    ) -> None:
        super().__init__(master, bg=fill)
        self._radius = radius
        self._fill = fill
        self._border = border
        self._accent = accent
        self._canvas = tk.Canvas(self, bg=parent_bg, highlightthickness=0, bd=0)
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


class RoundedEntry(RoundedCard):
    """Entry field inside a rounded border."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        textvariable: tk.StringVar,
        font: FontSpec,
        readonly: bool = False,
        parent_bg: str = BG,
        fill: str = CARD,
        border: str = BORDER,
    ) -> None:
        super().__init__(master, radius=14, fill=fill, border=border, parent_bg=parent_bg)
        self.configure(height=48)
        self.grid_propagate(False)
        self.columnconfigure(0, weight=1)
        self.entry = tk.Entry(
            self,
            textvariable=textvariable,
            state="readonly" if readonly else "normal",
            bg=fill,
            readonlybackground=fill,
            fg=TEXT,
            insertbackground=TEXT,
            selectbackground=PURPLE,
            selectforeground=TEXT,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=font,
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=14, pady=10)
