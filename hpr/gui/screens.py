from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from tkinter import ttk
from typing import TYPE_CHECKING

from hpr.find_downloads import latest_reengagement_csv
from hpr.gui.state import GuiState
from hpr.gui.theme import (
    BLUE,
    DANGER_BG,
    INFO_BG,
    PURPLE,
    RED,
    SUCCESS_BG,
    TEAL,
    FontSpec,
)
from hpr.gui.widgets import RoundedButton, RoundedCard


class Screens:
    """Render wizard screens."""

    content: ttk.Frame
    hosted_var: tk.StringVar
    lastweek_var: tk.StringVar
    outdir_var: tk.StringVar
    date_var: tk.StringVar
    native_pivot_var: tk.BooleanVar
    data: GuiState
    font_body: FontSpec
    _options_open: bool
    _options_toggle: ttk.Button | None
    _options_body: RoundedCard
    _primary_btn: RoundedButton
    _handoff_buttons: list[RoundedButton]
    _primary_action: Callable[[], None] | None
    _back_action: Callable[[], None] | None

    if TYPE_CHECKING:

        def _begin_step(self, number: int) -> None: ...

        def _accent_button(
            self,
            parent: tk.Misc,
            text: str,
            command: Callable[[], None],
            *,
            min_width: int = 0,
        ) -> RoundedButton: ...

        def _ghost_button(
            self,
            parent: tk.Misc,
            text: str,
            command: Callable[[], None],
        ) -> RoundedButton: ...

        def _browse_hosted(self) -> None: ...
        def _browse_lastweek(self) -> None: ...
        def _browse_outdir(self) -> None: ...
        def _start_handoff(self) -> None: ...
        def _copy_again(self) -> None: ...
        def _browse_reactivated(self) -> None: ...
        def _choose_reactivated(self, path: Path) -> None: ...
        def _start_build(self) -> None: ...
        def _open_log(self) -> None: ...
        def _show_qa_report(self) -> None: ...
        def _open_workbook(self) -> None: ...
        def _start_over(self) -> None: ...
        def destroy(self) -> None: ...

    def render_inputs(self) -> None:
        """Render step 1: input selection."""

        self._begin_step(1)
        frame = self.content
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Upload reports", style="Heading.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 4)
        )
        ttk.Label(
            frame,
            text="Select Hosted Players CSV and last week's workbook to find Reactivated Players.",
            style="Muted.TLabel",
            wraplength=620,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 22))

        ttk.Label(frame, text="Hosted Players Report").grid(row=2, column=0, columnspan=3, sticky="w")
        ttk.Entry(frame, textvariable=self.hosted_var, state="readonly").grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(5, 14), padx=(0, 12)
        )
        hosted_button = self._ghost_button(frame, "Browse…", self._browse_hosted)
        hosted_button.grid(row=3, column=2, sticky="e", pady=(5, 14))

        ttk.Label(frame, text="Last week's workbook").grid(row=4, column=0, columnspan=3, sticky="w")
        ttk.Entry(frame, textvariable=self.lastweek_var, state="readonly").grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(5, 14), padx=(0, 12)
        )
        prior_button = self._ghost_button(frame, "Browse…", self._browse_lastweek)
        prior_button.grid(row=5, column=2, sticky="e", pady=(5, 14))

        self._build_options_section(frame, toggle_row=6, body_row=7)

        self._primary_btn = self._accent_button(frame, "Find reactivated players", self._start_handoff)
        self._primary_btn.grid(row=8, column=0, columnspan=3, sticky="e", pady=(22, 10))
        self._handoff_buttons = [hosted_button, prior_button, self._primary_btn]
        self._primary_action = self._start_handoff

    def _build_options_section(self, frame: ttk.Frame, toggle_row: int, body_row: int) -> None:
        """Dropdown options."""

        chevron = "▾" if self._options_open else "▸"
        self._options_toggle = ttk.Button(
            frame,
            text=f"{chevron}  Options",
            style="Link.TButton",
            takefocus=True,
            command=self._toggle_options,
        )
        self._options_toggle.bind("<Return>", self._toggle_options_key)
        self._options_toggle.grid(row=toggle_row, column=0, columnspan=3, sticky="w", pady=(10, 0))

        card = RoundedCard(frame)
        card.columnconfigure(1, weight=1)
        card.grid(row=body_row, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        self._options_body = card
        ttk.Label(card, text="Report date", style="Muted.TLabel").grid(
            row=0, column=0, sticky="w", padx=(16, 10), pady=(16, 10)
        )
        ttk.Entry(card, textvariable=self.date_var, width=16).grid(row=0, column=1, sticky="w", pady=(16, 10))
        ttk.Label(card, text="Output folder", style="Muted.TLabel").grid(
            row=1, column=0, sticky="w", padx=(16, 10), pady=(0, 10)
        )
        ttk.Entry(card, textvariable=self.outdir_var).grid(row=1, column=1, sticky="ew", pady=(0, 10), padx=(0, 10))
        self._ghost_button(card, "Browse…", self._browse_outdir).grid(
            row=1, column=2, sticky="e", pady=(0, 10), padx=(0, 16)
        )
        ttk.Checkbutton(
            card,
            text="Create Pivot Tables",
            variable=self.native_pivot_var,
        ).grid(row=2, column=0, columnspan=3, sticky="w", padx=16, pady=(0, 16))

        if not self._options_open:
            self._options_body.grid_remove()

    def _toggle_options(self) -> None:
        assert self._options_toggle is not None
        self._options_open = not self._options_open
        if self._options_open:
            self._options_body.grid()
            self._options_toggle.config(text="▾  Options")
            return
        self._options_body.grid_remove()
        self._options_toggle.config(text="▸  Options")

    def _toggle_options_key(self, _event: tk.Event[ttk.Button] | None) -> str:
        self._toggle_options()
        return "break"

    def render_clipboard(self) -> None:
        """Step 2: Tableau clipboard handoff."""

        self._begin_step(2)
        frame = self.content
        frame.columnconfigure(0, weight=1)

        failed = bool(self.data.missing_uids) and not self.data.clipboard_ok
        status = RoundedCard(
            frame,
            fill=DANGER_BG if failed else SUCCESS_BG,
            border=RED if failed else TEAL,
            accent=RED if failed else TEAL,
        )
        status.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        if not self.data.missing_uids:
            status_text = "No missing UIDs found"
        elif self.data.clipboard_ok:
            status_text = f"✓  {self.data.missing_prior_row_count} prior-workbook rows copied to your clipboard"
        else:
            status_text = "Couldn't copy to your clipboard"
        ttk.Label(
            status,
            text=status_text,
            style="DangerCardHeading.TLabel" if failed else "SuccessCardHeading.TLabel",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 14))

        instruction_intro = (
            "No Tableau clipboard handoff is needed for this run."
            if not self.data.missing_uids
            else "Now hand the UIDs to Tableau:"
        )
        ttk.Label(frame, text=instruction_intro, style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(0, 12))
        instruction_text = (
            "1.   Download the Reactivated Players CSV if Tableau has one for this week\n"
            "2.   Click Continue when it's downloaded"
            if not self.data.missing_uids
            else (
                "1.   Paste the UIDs into Tableau\n"
                "2.   Download the Reactivated Players CSV\n"
                "3.   Click Continue when it's downloaded"
            )
        )
        ttk.Label(frame, text=instruction_text, font=self.font_body, justify="left").grid(
            row=2, column=0, sticky="w", pady=(0, 22)
        )

        card = RoundedCard(frame, accent=BLUE)
        card.columnconfigure(0, weight=1)
        card.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        ttk.Label(card, text="LOST THEM?", style="Caption.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 2)
        )
        ttk.Label(
            card,
            text="Re-copy the UIDs, or grab them from the hidden “Copy” sheet in the final workbook.",
            style="Muted.TLabel",
            wraplength=470,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))
        self._ghost_button(card, "Copy UIDs", self._copy_again).grid(row=1, column=1, padx=(12, 16), pady=(0, 14))

        nav = ttk.Frame(frame)
        nav.grid(row=4, column=0, sticky="ew")
        nav.columnconfigure(0, weight=1)
        self._ghost_button(nav, "←  Back", self.render_inputs).grid(row=0, column=0, sticky="w")
        self._accent_button(nav, "Continue  →", self.render_reactivated).grid(row=0, column=1, sticky="e")
        self._primary_action = self.render_reactivated
        self._back_action = self.render_inputs

    def render_reactivated(self) -> None:
        """Step 3: CSV selection."""

        self._begin_step(3)
        frame = self.content
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Add the Reactivated Players CSV", style="Heading.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        ttk.Label(
            frame,
            text="Use the file you just downloaded from Tableau.",
            style="Muted.TLabel",
            wraplength=620,
        ).grid(row=1, column=0, sticky="w", pady=(0, 22))

        latest = latest_reengagement_csv()
        recent = RoundedCard(frame, accent=PURPLE)
        recent.columnconfigure(0, weight=1)
        recent.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        ttk.Label(recent, text="MOST RECENT DOWNLOAD", style="Caption.TLabel").grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 6)
        )
        if latest is not None:
            modified = datetime.fromtimestamp(latest.stat().st_mtime).strftime("%b %d, %Y · %I:%M %p")
            ttk.Label(recent, text=latest.name, style="Strong.TLabel").grid(row=1, column=0, sticky="w", padx=16)
            ttk.Label(recent, text=modified, style="Small.TLabel").grid(
                row=2, column=0, sticky="w", padx=16, pady=(2, 12)
            )
            self._accent_button(recent, "Use this file  →", lambda: self._choose_reactivated(latest)).grid(
                row=3, column=0, sticky="w", padx=16, pady=(0, 16)
            )
        else:
            ttk.Label(
                recent,
                text="No recent Re-Engagement CSV in your Downloads folder.",
                style="Muted.TLabel",
            ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 16))

        other = RoundedCard(frame)
        other.grid(row=3, column=0, sticky="ew", pady=(0, 22))
        ttk.Label(other, text="OR CHOOSE A DIFFERENT FILE", style="Caption.TLabel").grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 8)
        )
        self._ghost_button(other, "Browse…", self._browse_reactivated).grid(
            row=1, column=0, sticky="w", padx=16, pady=(0, 16)
        )

        self._ghost_button(frame, "←  Back", self.render_clipboard).grid(row=4, column=0, sticky="w")
        self._back_action = self.render_clipboard

    def render_build(self, error: str | None = None) -> None:
        """Step 4: build status."""

        self._begin_step(4)
        frame = self.content
        frame.columnconfigure(0, weight=1)

        if error is None:
            status = RoundedCard(frame, fill=INFO_BG, border=BLUE, accent=BLUE)
            status.grid(row=0, column=0, sticky="ew")
            ttk.Label(status, text="Creating report...", style="InfoCardHeading.TLabel").grid(
                row=0, column=0, sticky="w", padx=16, pady=(16, 4)
            )
            ttk.Label(status, text="This may take a moment.", style="InfoCardMuted.TLabel", wraplength=620).grid(
                row=1, column=0, sticky="w", padx=16, pady=(0, 16)
            )
            self._start_build()
            return

        status = RoundedCard(frame, fill=DANGER_BG, border=RED, accent=RED)
        status.grid(row=0, column=0, sticky="ew", pady=(0, 22))
        ttk.Label(status, text="Couldn't build the report", style="DangerCardHeading.TLabel").grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 6)
        )
        ttk.Label(status, text=error, style="DangerCardMuted.TLabel", wraplength=620, justify="left").grid(
            row=1, column=0, sticky="w", padx=16, pady=(0, 16)
        )
        nav = ttk.Frame(frame)
        nav.grid(row=1, column=0, sticky="ew")
        nav.columnconfigure(0, weight=1)
        self._ghost_button(nav, "←  Choose a different file", self.render_reactivated).grid(row=0, column=0, sticky="w")
        self._ghost_button(nav, "View log", self._open_log).grid(row=0, column=1, padx=(0, 10))
        self._accent_button(nav, "Try again", lambda: self.render_build(None)).grid(row=0, column=2, sticky="e")
        self._primary_action = lambda: self.render_build(None)
        self._back_action = self.render_reactivated

    def render_done(self) -> None:
        """Show finalized report."""

        self._begin_step(4)
        frame = self.content
        frame.columnconfigure(0, weight=1)
        result = self.data.result
        assert result is not None

        status = RoundedCard(frame, fill=SUCCESS_BG, border=TEAL, accent=TEAL)
        status.columnconfigure(1, weight=1)
        status.grid(row=0, column=0, sticky="ew")
        ttk.Label(status, text="✓  Success", style="SuccessCardHeading.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 2)
        )
        ttk.Label(status, text="Your report is ready.", style="SuccessCardMuted.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 16)
        )

        rows = [
            ("Final workbook", result.workbook_path.name),
            ("Market", result.market),
            ("Reactivated players", str(result.reactivated_player_count)),
        ]
        for index, (label, value) in enumerate(rows, start=2):
            ttk.Label(status, text=label, style="SuccessCardMuted.TLabel").grid(
                row=index, column=0, sticky="nw", padx=(16, 16), pady=4
            )
            ttk.Label(status, text=value, style="SuccessCard.TLabel", wraplength=440, justify="left").grid(
                row=index, column=1, sticky="w", padx=(0, 16), pady=4
            )

        actions = ttk.Frame(frame)
        actions.grid(row=1, column=0, sticky="ew", pady=(24, 0))
        actions.columnconfigure(1, weight=1)

        left_actions = ttk.Frame(actions)
        left_actions.grid(row=0, column=0, sticky="w")
        self._ghost_button(left_actions, "Start over", self._start_over).grid(row=0, column=0, padx=(0, 10))
        self._ghost_button(left_actions, "Close", self.destroy).grid(row=0, column=1)

        right_actions = ttk.Frame(actions)
        right_actions.grid(row=0, column=2, sticky="e")
        self._ghost_button(right_actions, "QA report", self._show_qa_report).grid(row=0, column=0, padx=(0, 10))
        self._accent_button(right_actions, "Open workbook", self._open_workbook).grid(row=0, column=1)
        self._primary_action = self._open_workbook
