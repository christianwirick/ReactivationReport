from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk
from typing import TYPE_CHECKING

from hpr.find_downloads import latest_reengagement_csv
from hpr.gui import text
from hpr.gui.state import GuiState
from hpr.gui.theme import (
    BLUE,
    BORDER,
    CARD,
    DANGER_BG,
    GRADIENT,
    INFO_BG,
    PURPLE,
    RED,
    SETTINGS_BG,
    SETTINGS_CARD,
    STEP_IDLE,
    SUCCESS_BANNER_DARK,
    SUCCESS_BG,
    TEAL,
    FontSpec,
)
from hpr.gui.widgets import (
    ButtonIcon,
    GradientBanner,
    GradientConnector,
    RoundedButton,
    RoundedCard,
    RoundedEntry,
    StepNumberChip,
)

FILE_CHIP_GRADIENT_RANGES = ((0.0, 0.4), (0.6, 1.0))
FILE_CONNECTOR_GRADIENT_RANGE = (0.4, 0.6)


class Screens:
    """Render wizard screens."""

    content: ttk.Frame
    content_shell: ttk.Frame
    content_canvas: tk.Canvas
    footer: ttk.Frame
    status_label: ttk.Label
    progress_label: ttk.Label
    hosted_var: tk.StringVar
    lastweek_var: tk.StringVar
    outdir_var: tk.StringVar
    date_var: tk.StringVar
    qa_var: tk.BooleanVar
    data: GuiState
    font_heading: FontSpec
    font_body: FontSpec
    font_body_bold: FontSpec
    font_small: FontSpec
    _primary_btn: RoundedButton
    _handoff_buttons: list[RoundedButton]
    _file_chips: list[StepNumberChip]
    _file_rows: list[tuple[ttk.Label, ttk.Label]]
    _file_connector: GradientConnector
    _file_chips_gradient: bool
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
            parent_bg: str = ...,
            min_width: int = 0,
        ) -> RoundedButton: ...

        def _ghost_button(
            self,
            parent: tk.Misc,
            text: str,
            command: Callable[[], None],
            *,
            parent_bg: str = ...,
            border_color: str | None = None,
            min_width: int = 0,
            min_height: int = 0,
            pad_x: int = 20,
            pad_y: int = 11,
            fill: str = ...,
            fill_hover: str = ...,
            fill_press: str = ...,
            icon: ButtonIcon | None = None,
        ) -> RoundedButton: ...

        def _browse_hosted(self) -> None: ...
        def _browse_lastweek(self) -> None: ...
        def _browse_outdir(self) -> None: ...
        def _schedule_file_chip_gradient(self) -> None: ...
        def _start_handoff(self) -> None: ...
        def _copy_again(self) -> None: ...
        def _browse_reactivated(self) -> None: ...
        def _choose_reactivated(self, path: Path) -> None: ...
        def _start_build(self) -> None: ...
        def _open_log(self) -> None: ...
        def _show_qa_report(self) -> None: ...
        def _open_workbook(self) -> None: ...
        def _start_over(self) -> None: ...

    def render_inputs(self) -> None:
        """Render step 1: input selection."""

        self._begin_step(1)
        frame = self.content
        frame.columnconfigure(0, weight=1)

        card = RoundedCard(frame, fill=CARD, border=BORDER)
        card.columnconfigure(1, weight=1)
        card.grid(row=0, column=0, sticky="ew")

        ttk.Label(card, text=text.ADD_REPORTS_HEADING, style="CardHeading.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=(22, 0), pady=(22, 3)
        )
        settings_button = self._ghost_button(
            card,
            "",
            self.render_settings,
            parent_bg=CARD,
            border_color=BORDER,
            min_width=52,
            min_height=52,
            pad_x=15,
            icon="gear",
        )
        settings_button.grid(row=0, column=2, sticky="ne", padx=20, pady=18)

        choices: tuple[tuple[tk.StringVar, str, str, Callable[[], None]], ...] = (
            (
                self.hosted_var,
                text.HOSTED_PLAY_REPORT_LABEL,
                text.HOSTED_PLAY_REPORT_HINT,
                self._browse_hosted,
            ),
            (
                self.lastweek_var,
                text.LAST_WEEK_WORKBOOK_LABEL,
                text.LAST_WEEK_WORKBOOK_HINT,
                self._browse_lastweek,
            ),
        )
        file_buttons: list[RoundedButton] = []
        file_chips: list[StepNumberChip] = []
        file_rows: list[tuple[ttk.Label, ttk.Label]] = []
        for index, (variable, label, hint, browse) in enumerate(choices, start=1):
            row = index * 2 - 1
            row_padding = (16, 0) if index == 1 else (0, 2)
            selected_path = variable.get().strip()
            selected = bool(selected_path)
            chip = StepNumberChip(
                card,
                "✓" if selected else index,
                font=self.font_body_bold,
                fill=TEAL if selected else STEP_IDLE,
                background=CARD,
                diameter=40,
            )
            if selected and self._file_chips_gradient:
                chip.set_vertical_gradient(*FILE_CHIP_GRADIENT_RANGES[index - 1])
            chip.grid(
                row=row,
                column=0,
                sticky="s" if index == 1 else "n",
                padx=(22, 18),
                pady=row_padding,
            )
            file_chips.append(chip)

            details = ttk.Frame(card, style="Card.TFrame")
            details.grid(row=row, column=1, sticky="ew", pady=row_padding)
            details.columnconfigure(0, weight=1)
            title_label = ttk.Label(
                details,
                text=Path(selected_path).name if selected else label,
                style="CardStrong.TLabel",
                wraplength=430,
            )
            title_label.grid(row=0, column=0, sticky="w")
            hint_label = ttk.Label(details, text=hint, style="CardMuted.TLabel")
            hint_label.grid(row=1, column=0, sticky="w", pady=(1, 0))
            if selected:
                hint_label.grid_remove()
            file_rows.append((title_label, hint_label))

            action = self._ghost_button(
                card,
                "",
                browse,
                parent_bg=CARD,
                border_color=BORDER,
                min_width=52,
                min_height=48,
                pad_x=14,
                icon="folder",
            )
            action.grid(row=row, column=2, sticky="e", padx=(12, 22), pady=row_padding)
            file_buttons.append(action)

            if index == 1:
                connector = TEAL if selected else STEP_IDLE
                self._file_connector = GradientConnector(
                    card,
                    fill=connector,
                    background=CARD,
                )
                if self._file_chips_gradient:
                    self._file_connector.set_vertical_gradient(*FILE_CONNECTOR_GRADIENT_RANGE)
                self._file_connector.grid(row=row + 1, column=0)

        self._primary_btn = self._accent_button(
            card,
            text.CONTINUE_BUTTON,
            self._start_handoff,
            parent_bg=CARD,
            min_width=132,
        )
        self._primary_btn.grid(row=4, column=0, columnspan=3, sticky="e", padx=22, pady=(22, 22))
        self._file_chips = file_chips
        self._file_rows = file_rows
        self._handoff_buttons = [settings_button, *file_buttons, self._primary_btn]
        self._primary_action = self._start_handoff
        self._schedule_file_chip_gradient()

    def _refresh_file_rows(self) -> None:
        """Refresh Step 1 file state in place after a dialog selection."""

        choices = (
            (self.hosted_var, text.HOSTED_PLAY_REPORT_LABEL, text.HOSTED_PLAY_REPORT_HINT),
            (self.lastweek_var, text.LAST_WEEK_WORKBOOK_LABEL, text.LAST_WEEK_WORKBOOK_HINT),
        )
        self._file_chips_gradient = False
        for index, ((variable, label, hint), chip, (title_label, hint_label)) in enumerate(
            zip(choices, self._file_chips, self._file_rows, strict=True),
            start=1,
        ):
            selected_path = variable.get().strip()
            selected = bool(selected_path)
            chip.set_solid("✓" if selected else index, TEAL if selected else STEP_IDLE)
            title_label.configure(text=Path(selected_path).name if selected else label)
            if selected:
                hint_label.grid_remove()
            else:
                hint_label.configure(text=hint)
                hint_label.grid()

        self._file_connector.set_solid(TEAL if self.hosted_var.get().strip() else STEP_IDLE)
        self._schedule_file_chip_gradient()

    def render_settings(self) -> None:
        """Render Step 1 settings as a separate page."""

        self._begin_step(1)
        frame = self.content
        self.content_shell.configure(style="Settings.TFrame")
        self.content_canvas.configure(bg=SETTINGS_BG)
        frame.configure(style="Settings.TFrame")
        self.footer.configure(style="Settings.TFrame")
        self.status_label.configure(style="SettingsSmall.TLabel")
        self.progress_label.configure(style="SettingsSmall.TLabel")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text=text.SETTINGS_HEADING, style="SettingsHeading.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        close_button = self._ghost_button(
            frame,
            "",
            self.render_inputs,
            parent_bg=SETTINGS_BG,
            border_color=STEP_IDLE,
            min_width=52,
            min_height=52,
            pad_x=15,
            fill=SETTINGS_CARD,
            fill_hover=STEP_IDLE,
            fill_press=SETTINGS_BG,
            icon="close",
        )
        close_button.grid(row=0, column=2, rowspan=2, sticky="ne")
        ttk.Label(
            frame,
            text=text.SETTINGS_SUBTITLE,
            style="SettingsMuted.TLabel",
            wraplength=620,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 22))

        settings_card = RoundedCard(
            frame,
            fill=SETTINGS_CARD,
            border=STEP_IDLE,
            parent_bg=SETTINGS_BG,
        )
        settings_card.columnconfigure(1, weight=1)
        settings_card.grid(row=2, column=0, columnspan=3, sticky="ew")

        ttk.Label(settings_card, text=text.REPORT_DATE_LABEL, style="SettingsCard.TLabel").grid(
            row=0, column=0, sticky="w", padx=(18, 24), pady=16
        )
        RoundedEntry(
            settings_card,
            textvariable=self.date_var,
            font=self.font_body,
            parent_bg=SETTINGS_CARD,
            fill=SETTINGS_BG,
            border=STEP_IDLE,
        ).grid(row=0, column=1, columnspan=2, sticky="ew", padx=(0, 18), pady=12)

        tk.Frame(settings_card, background=STEP_IDLE, height=1).grid(
            row=1, column=0, columnspan=3, sticky="ew", padx=18
        )

        ttk.Label(settings_card, text=text.OUTPUT_FOLDER_LABEL, style="SettingsCard.TLabel").grid(
            row=2, column=0, sticky="w", padx=(18, 24), pady=16
        )
        RoundedEntry(
            settings_card,
            textvariable=self.outdir_var,
            font=self.font_body,
            parent_bg=SETTINGS_CARD,
            fill=SETTINGS_BG,
            border=STEP_IDLE,
        ).grid(row=2, column=1, sticky="ew", padx=(0, 12), pady=12)
        self._ghost_button(
            settings_card,
            "",
            self._browse_outdir,
            parent_bg=SETTINGS_CARD,
            border_color=STEP_IDLE,
            min_width=58,
            min_height=48,
            pad_x=17,
            fill=SETTINGS_BG,
            fill_hover=STEP_IDLE,
            fill_press=SETTINGS_CARD,
            icon="folder",
        ).grid(row=2, column=2, sticky="e", padx=(0, 18), pady=12)

        tk.Frame(settings_card, background=STEP_IDLE, height=1).grid(
            row=3, column=0, columnspan=3, sticky="ew", padx=18
        )

        ttk.Checkbutton(
            settings_card,
            text=text.QA_OPTION,
            variable=self.qa_var,
            style="SettingsCard.TCheckbutton",
        ).grid(row=4, column=0, columnspan=3, sticky="w", padx=18, pady=16)

        self._primary_action = self.render_inputs
        self._back_action = self.render_inputs

    def render_clipboard(self) -> None:
        """Step 2: Tableau clipboard handoff."""

        self._begin_step(2)
        frame = self.content
        frame.columnconfigure(0, weight=1)

        failed = bool(self.data.missing_uids) and not self.data.clipboard_ok
        copied = bool(self.data.missing_uids) and self.data.clipboard_ok
        if not self.data.missing_uids:
            status_text = text.NO_MISSING_UIDS_HEADING
        elif copied:
            status_text = text.copied_uids_heading(self.data.missing_prior_row_count)
        else:
            status_text = text.CLIPBOARD_FAILURE_HEADING
        if copied:
            GradientBanner(
                frame,
                status_text,
                font=self.font_heading,
                colors=(CARD, CARD),
                height=68,
                text_color=TEAL,
            ).grid(row=0, column=0, sticky="ew", pady=(0, 16))
        else:
            status = RoundedCard(
                frame,
                fill=DANGER_BG if failed else SUCCESS_BG,
                border=RED if failed else TEAL,
                accent=RED if failed else TEAL,
            )
            status.grid(row=0, column=0, sticky="ew", pady=(0, 16))
            ttk.Label(
                status,
                text=status_text,
                style="DangerCardHeading.TLabel" if failed else "SuccessCardHeading.TLabel",
            ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 14))

        if copied:
            instructions = (
                text.PASTE_UIDS_INSTRUCTION,
                text.DOWNLOAD_CSV_INSTRUCTION,
                text.RETURN_CONTINUE_INSTRUCTION,
            )
            instruction_card = RoundedCard(frame, fill=CARD)
            instruction_card.columnconfigure(1, weight=1)
            instruction_card.grid(row=1, column=0, sticky="ew", pady=(0, 20))
            for index, instruction in enumerate(instructions, start=1):
                padding = (18, 6) if index == 1 else ((6, 6) if index == 2 else (6, 18))
                StepNumberChip(
                    instruction_card,
                    index,
                    font=self.font_body_bold,
                    fill=PURPLE,
                    background=CARD,
                ).grid(
                    row=index - 1,
                    column=0,
                    sticky="w",
                    padx=(20, 12),
                    pady=padding,
                )
                ttk.Label(
                    instruction_card,
                    text=instruction,
                    style="CardStrong.TLabel",
                    wraplength=430,
                ).grid(
                    row=index - 1,
                    column=1,
                    sticky="w",
                    pady=padding,
                )

            tk.Frame(instruction_card, background=BORDER, width=1).grid(
                row=0,
                column=2,
                rowspan=3,
                sticky="ns",
                padx=24,
                pady=20,
            )
            self._ghost_button(
                instruction_card,
                text.COPY_UIDS_BUTTON,
                self._copy_again,
                parent_bg=CARD,
                border_color=BORDER,
            ).grid(row=0, column=3, rowspan=3, padx=(0, 20), pady=20)
            nav_row = 2
        else:
            content_row = 1
            if not self.data.missing_uids:
                ttk.Label(frame, text=text.NO_CLIPBOARD_HANDOFF, style="Muted.TLabel").grid(
                    row=content_row, column=0, sticky="w", pady=(0, 12)
                )
                content_row += 1
            instruction_text = (
                text.ZERO_MISSING_INSTRUCTIONS if not self.data.missing_uids else text.TABLEAU_HANDOFF_INSTRUCTIONS
            )
            ttk.Label(frame, text=instruction_text, font=self.font_body, justify="left").grid(
                row=content_row, column=0, sticky="w", pady=(0, 22)
            )
            content_row += 1
            card = RoundedCard(frame, accent=BLUE)
            card.columnconfigure(0, weight=1)
            card.grid(row=content_row, column=0, sticky="ew", pady=(0, 20))
            ttk.Label(card, text=text.LOST_UIDS_CAPTION, style="Caption.TLabel").grid(
                row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 2)
            )
            ttk.Label(
                card,
                text="",
                style="Muted.TLabel",
                wraplength=470,
                justify="left",
            ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))
            self._ghost_button(card, text.COPY_BUTTON, self._copy_again).grid(
                row=1,
                column=1,
                padx=(12, 16),
                pady=(0, 14),
            )
            nav_row = content_row + 1

        nav = ttk.Frame(frame)
        nav.grid(row=nav_row, column=0, sticky="ew")
        nav.columnconfigure(0, weight=1)
        self._ghost_button(nav, text.BACK_BUTTON, self.render_inputs).grid(row=0, column=0, sticky="w")
        self._accent_button(nav, text.CONTINUE_ARROW_BUTTON, self.render_reactivated).grid(row=0, column=1, sticky="e")
        self._primary_action = self.render_reactivated
        self._back_action = self.render_inputs

    def render_reactivated(self) -> None:
        """Step 3: CSV selection."""

        self._begin_step(3)
        frame = self.content
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text=text.SELECT_EXPORT_HEADING, style="Heading.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )

        latest = latest_reengagement_csv()
        recent = RoundedCard(frame, fill=CARD, border=BORDER)
        recent.columnconfigure(1, weight=1)
        recent.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        if latest is not None:
            modified = text.recent_download_modified(latest.stat().st_mtime)
            ttk.Label(
                recent,
                text=latest.name,
                style="CardStrong.TLabel",
                wraplength=600,
            ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 2))
            ttk.Label(recent, text=modified, style="CardMuted.TLabel").grid(
                row=1, column=0, columnspan=2, sticky="w", padx=20
            )
            self._accent_button(
                recent,
                text.USE_RECENT_FILE_BUTTON,
                lambda: self._choose_reactivated(latest),
                parent_bg=CARD,
                min_width=150,
            ).grid(row=2, column=0, sticky="w", padx=(20, 8), pady=(20, 20))
            self._ghost_button(
                recent,
                "",
                self._browse_reactivated,
                parent_bg=CARD,
                border_color=BORDER,
                min_width=52,
                pad_x=14,
                icon="folder",
            ).grid(row=2, column=1, sticky="w", pady=(20, 20))
        else:
            ttk.Label(
                recent,
                text=text.NO_RECENT_DOWNLOAD,
                style="CardMuted.TLabel",
                wraplength=600,
            ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 12))
            self._ghost_button(
                recent,
                "",
                self._browse_reactivated,
                parent_bg=CARD,
                border_color=BORDER,
                min_width=52,
                pad_x=14,
                icon="folder",
            ).grid(row=1, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 20))

        self._ghost_button(frame, text.BACK_BUTTON, self.render_clipboard).grid(row=2, column=0, sticky="w")
        self._back_action = self.render_clipboard

    def render_build(self, error: str | None = None) -> None:
        """Step 4: build status."""

        self._begin_step(4)
        frame = self.content
        frame.columnconfigure(0, weight=1)

        if error is None:
            status = RoundedCard(frame, fill=INFO_BG, border=BLUE, accent=BLUE)
            status.grid(row=0, column=0, sticky="ew")
            ttk.Label(status, text=text.BUILD_BUSY, style="InfoCardHeading.TLabel").grid(
                row=0, column=0, sticky="w", padx=16, pady=(16, 4)
            )
            ttk.Label(status, text=text.BUILD_WAIT_SUBTITLE, style="InfoCardMuted.TLabel", wraplength=620).grid(
                row=1, column=0, sticky="w", padx=16, pady=(0, 16)
            )
            self._start_build()
            return

        status = RoundedCard(frame, fill=DANGER_BG, border=RED, accent=RED)
        status.grid(row=0, column=0, sticky="ew", pady=(0, 22))
        ttk.Label(status, text=text.BUILD_FAILURE_HEADING, style="DangerCardHeading.TLabel").grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 6)
        )
        ttk.Label(status, text=error, style="DangerCardMuted.TLabel", wraplength=620, justify="left").grid(
            row=1, column=0, sticky="w", padx=16, pady=(0, 16)
        )
        nav = ttk.Frame(frame)
        nav.grid(row=1, column=0, sticky="ew")
        nav.columnconfigure(0, weight=1)
        self._ghost_button(nav, text.CHOOSE_DIFFERENT_FILE_BUTTON, self.render_reactivated).grid(
            row=0, column=0, sticky="w"
        )
        self._ghost_button(nav, text.VIEW_LOG_BUTTON, self._open_log).grid(row=0, column=1, padx=(0, 10))
        self._accent_button(nav, text.TRY_AGAIN_BUTTON, lambda: self.render_build(None)).grid(
            row=0, column=2, sticky="e"
        )
        self._primary_action = lambda: self.render_build(None)
        self._back_action = self.render_reactivated

    def render_done(self) -> None:
        """Show finalized report."""

        self._begin_step(4)
        frame = self.content
        frame.columnconfigure(0, weight=1)
        result = self.data.result
        assert result is not None

        GradientBanner(
            frame,
            text.SUCCESS_HEADING,
            font=self.font_heading,
            colors=(SUCCESS_BANNER_DARK, *GRADIENT),
            height=84,
            text_color=TEAL,
        ).grid(row=0, column=0, sticky="ew", pady=(0, 16))

        details = RoundedCard(frame, fill=CARD)
        details.columnconfigure(1, weight=1)
        details.grid(row=1, column=0, sticky="ew")

        rows = [
            (text.FINAL_WORKBOOK_LABEL, result.workbook_path.name),
            (text.MARKET_LABEL, result.market),
            (text.REACTIVATED_PLAYERS_LABEL, str(result.reactivated_player_count)),
        ]
        for index, (label, value) in enumerate(rows):
            content_row = index * 2
            ttk.Label(details, text=label, style="CardMuted.TLabel").grid(
                row=content_row, column=0, sticky="nw", padx=(16, 16), pady=12
            )
            ttk.Label(
                details,
                text=value,
                style="Card.TLabel",
                wraplength=440,
                anchor="e",
                justify="right",
            ).grid(row=content_row, column=1, sticky="ew", padx=(0, 16), pady=12)
            if index < len(rows) - 1:
                tk.Frame(details, background=BORDER, height=1).grid(
                    row=content_row + 1, column=0, columnspan=2, sticky="ew", padx=16
                )

        actions = ttk.Frame(frame)
        actions.grid(row=2, column=0, sticky="ew", pady=(24, 0))
        actions.columnconfigure(1, weight=1)

        self._ghost_button(
            actions,
            "",
            self._start_over,
            border_color=BORDER,
            min_width=48,
            min_height=48,
            pad_x=13,
            icon="back",
        ).grid(row=0, column=0, sticky="w")

        right_actions = ttk.Frame(actions)
        right_actions.grid(row=0, column=2, sticky="e")
        self._ghost_button(right_actions, text.QA_TITLE, self._show_qa_report).grid(row=0, column=0, padx=(0, 10))
        self._accent_button(right_actions, text.OPEN_WORKBOOK_BUTTON, self._open_workbook).grid(row=0, column=1)
        self._primary_action = self._open_workbook
        self._back_action = self._start_over
