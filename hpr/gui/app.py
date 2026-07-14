"""Wizard GUI & app entry point."""

from __future__ import annotations

import ctypes
import platform
import queue
import subprocess
import tkinter as tk
from collections.abc import Callable
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from types import TracebackType

from hpr._version import __version__
from hpr.assets import default_logo_path, default_theme_path
from hpr.clean import clean_runtime_artifacts
from hpr.clipboard import copy_text_to_clipboard
from hpr.errors import HostedPlayersReportError, InputValidationError, MarketInferenceError, WorkbookLockedError
from hpr.gui import text
from hpr.gui.run_jobs import AsyncRunner, ProgressController
from hpr.gui.screens import Screens
from hpr.gui.state import GuiState, HandoffWorkResult
from hpr.gui.theme import (
    BG,
    CARD,
    CARD_HOVER,
    DIVIDER,
    HEADER_BG,
    PURPLE,
    PURPLE_LIGHT,
    PURPLE_PRESS,
    SUNK,
    TEXT,
    WHITE,
    apply_styles,
)
from hpr.gui.widgets import RoundedButton, RoundedProgressBar, Stepper, scroll_needed
from hpr.logs import configure_logging, install_excepthooks
from hpr.read_tableau import read_reactivated_players_csv
from hpr.report.run import ReportResult, parse_report_date, run_report, run_uid_handoff
from hpr.settings import (
    Settings,
    default_output_folder,
    load_settings,
    save_settings,
)

APP_TITLE = text.APP_TITLE
APP_VERSION = __version__
MAX_BUILD_ATTEMPTS = 3
PROGRESS_TICK_MS = 33
PROGRESS_STEP = 2.0
PROGRESS_FINISH_STEP = 12.0


def open_in_os(path: Path) -> None:
    """Open file/folder with default system app."""

    if platform.system() == "Windows":
        import os

        os.startfile(str(path))  # type: ignore[attr-defined]
    elif platform.system() == "Darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def _enable_windows_dpi_awareness() -> None:
    """Enable sharpening on high-DPI displays."""

    if platform.system() != "Windows":
        return
    try:
        windll = getattr(ctypes, "windll", None)
        if windll is not None:
            windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


class HostedPlayersReportApp(Screens, tk.Tk):
    """Controller managing the four-step wizard."""

    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_TITLE}  v{APP_VERSION}")
        self.minsize(820, 540)

        self.log_session = configure_logging()
        self.log = self.log_session.logger
        self._settings: Settings = load_settings()
        self.log.info(
            "Started v%s | Python %s | %s",
            APP_VERSION,
            platform.python_version(),
            platform.platform(),
        )
        self._set_window_icon()

        self.hosted_var = tk.StringVar()
        self.lastweek_var = tk.StringVar()
        self.outdir_var = tk.StringVar(value=self._settings["output_folder"])
        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.native_pivot_var = tk.BooleanVar(value=self._settings["create_pivot"])

        self.data = GuiState()
        self.theme_path: Path = default_theme_path()
        self._options_open = False
        self._options_toggle: ttk.Button | None = None
        self._handoff_buttons: list[RoundedButton] = []
        self._primary_action: Callable[[], None] | None = None
        self._back_action: Callable[[], None] | None = None
        self.async_runner: AsyncRunner | None = None
        self.progress_controller: ProgressController | None = None
        self._stage_queue: queue.Queue[str] | None = None

        fonts = apply_styles(self)
        self.font_title = fonts.title
        self.font_heading = fonts.heading
        self.font_body = fonts.body
        self.font_body_bold = fonts.body_bold
        self.font_small = fonts.small
        self._build_chrome()
        self.render_inputs()
        self.bind("<Return>", self._on_return)
        self.bind("<Escape>", self._on_escape)
        self.protocol("WM_DELETE_WINDOW", self._request_close)
        self._center_window()

    def _center_window(self) -> None:
        """Center the window near the top of the display."""

        self.update_idletasks()
        width, height = 860, 660
        x = max(0, (self.winfo_screenwidth() - width) // 2)
        y = max(0, (self.winfo_screenheight() - height) // 3)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _set_window_icon(self) -> None:
        """Set icon when available."""

        try:
            logo = default_logo_path()
            if logo is not None:
                self._icon_image = tk.PhotoImage(file=str(logo))
                self.iconphoto(True, self._icon_image)
        except Exception:
            self.log.debug("Could not set the window icon", exc_info=True)

    def _open_log(self) -> None:

        try:
            open_in_os(self.log_session.log_path)
        except Exception:
            self.log.debug("Could not open the log file", exc_info=True)

    def destroy(self) -> None:
        """Release global bindings and close the window."""

        if self.progress_controller is not None:
            self.progress_controller.set_busy(False)
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            try:
                self.unbind_all(sequence)
            except tk.TclError:
                pass
        super().destroy()

    def _request_close(self) -> None:
        """Keep process alive while report is running."""

        busy = self.progress_controller.animating if self.progress_controller is not None else False
        if busy:
            messagebox.showinfo(APP_TITLE, text.WORK_IN_PROGRESS, parent=self)
            return
        self.destroy()

    def _on_return(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        """Run primary action when app is idle."""

        busy = self.progress_controller.animating if self.progress_controller is not None else False
        if not busy and self._primary_action is not None:
            self._primary_action()

    def _on_escape(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        """Run back action when app is idle."""

        busy = self.progress_controller.animating if self.progress_controller is not None else False
        if not busy and self._back_action is not None:
            self._back_action()

    def _persist_settings(self) -> None:

        self._settings["output_folder"] = self.outdir_var.get().strip()
        self._settings["create_pivot"] = bool(self.native_pivot_var.get())
        save_settings(self._settings)

    def report_callback_exception(
        self,
        exc: type[BaseException],
        value: BaseException,
        tb: TracebackType | None,
    ) -> None:
        """Log an unhandled Tk callback error."""

        self.log.error("Unhandled callback exception", exc_info=(exc, value, tb))
        try:
            messagebox.showerror(APP_TITLE, text.callback_error(value, self.log_session.log_path))
        except Exception:
            pass

    def _accent_button(
        self,
        parent: tk.Misc,
        text_value: str,
        command: Callable[[], None],
        *,
        min_width: int = 0,
    ) -> RoundedButton:
        """Create primary action button."""

        return RoundedButton(
            parent,
            text_value,
            command,
            parent_bg=BG,
            fill=PURPLE,
            fill_hover=PURPLE_LIGHT,
            fill_press=PURPLE_PRESS,
            text_color=WHITE,
            font=self.font_body_bold,
            min_width=min_width,
        )

    def _ghost_button(
        self,
        parent: tk.Misc,
        text_value: str,
        command: Callable[[], None],
    ) -> RoundedButton:
        """Secondary action button."""

        return RoundedButton(
            parent,
            text_value,
            command,
            parent_bg=BG,
            fill=CARD,
            fill_hover=CARD_HOVER,
            fill_press=SUNK,
            text_color=TEXT,
            font=self.font_body_bold,
        )

    def _build_chrome(self) -> None:
        header = ttk.Frame(self, style="Header.TFrame", padding=(28, 22, 28, 16))
        header.pack(fill="x")
        header.columnconfigure(1, weight=1)

        text_column = 0
        try:
            logo = default_logo_path()
            if logo is not None:
                raw_logo = tk.PhotoImage(file=str(logo))
                self._header_logo_source = raw_logo
                factor = max(1, raw_logo.height() // 46)
                self._header_logo = raw_logo.subsample(factor, factor)
                tk.Label(header, image=self._header_logo, bg=HEADER_BG, bd=0).grid(
                    row=0, column=0, rowspan=2, sticky="w", padx=(0, 14)
                )
                text_column = 1
        except Exception:
            self.log.debug("Could not load header logo", exc_info=True)

        ttk.Label(header, text=APP_TITLE, style="Title.TLabel").grid(row=0, column=text_column, sticky="w")
        self.stepper = Stepper(header, font=self.font_small)
        self.stepper.grid(row=1, column=text_column, sticky="w", pady=(2, 0))

        tk.Frame(self, background=DIVIDER, height=1).pack(fill="x")

        self.content_shell = ttk.Frame(self)
        self.content_shell.pack(fill="both", expand=True)
        self.content_shell.columnconfigure(0, weight=1)
        self.content_shell.rowconfigure(0, weight=1)

        self.content_canvas = tk.Canvas(self.content_shell, bg=BG, bd=0, highlightthickness=0, yscrollincrement=24)
        self.content_scrollbar = ttk.Scrollbar(self.content_shell, orient="vertical", command=self.content_canvas.yview)
        self.content_canvas.configure(yscrollcommand=self.content_scrollbar.set)
        self.content_canvas.grid(row=0, column=0, sticky="nsew")
        self.content_scrollbar.grid(row=0, column=1, sticky="ns")

        self.content = ttk.Frame(self.content_canvas, padding=(28, 26, 28, 16))
        self._content_window = self.content_canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", self._sync_content_scrollregion)
        self.content_canvas.bind("<Configure>", self._sync_content_width)
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>", self._on_mousewheel)
        self.bind_all("<Button-5>", self._on_mousewheel)

        footer = ttk.Frame(self, padding=(28, 12, 28, 20))
        footer.pack(fill="x", side="bottom")
        self.status_var = tk.StringVar(value="")
        ttk.Label(footer, textvariable=self.status_var, style="Small.TLabel").pack(side="left")
        self.progress = RoundedProgressBar(footer, width=260, height=12)
        self.progress_pct_var = tk.StringVar(value="")
        self.progress_label = ttk.Label(footer, textvariable=self.progress_pct_var, style="Small.TLabel")
        self.async_runner = AsyncRunner(self)
        self.progress_controller = ProgressController(
            self,
            status_var=self.status_var,
            progress=self.progress,
            percent_var=self.progress_pct_var,
            percent_label=self.progress_label,
            tick_ms=PROGRESS_TICK_MS,
            progress_step=PROGRESS_STEP,
            finish_step=PROGRESS_FINISH_STEP,
        )

    def _begin_step(self, number: int) -> None:
        self.stepper.set_step(number)
        self.set_busy(False)
        self._primary_action = None
        self._back_action = None
        for child in self.content.winfo_children():
            child.destroy()
        for column in range(3):
            self.content.columnconfigure(column, weight=0)
        self.content_canvas.yview_moveto(0)

    def _sync_content_scrollregion(self, _event: tk.Event[ttk.Frame] | None = None) -> None:
        bounds = self.content_canvas.bbox("all")
        self.content_canvas.configure(scrollregion=bounds)
        if scroll_needed(bounds, self.content_canvas.winfo_height()):
            self.content_scrollbar.grid()
        else:
            self.content_scrollbar.grid_remove()

    def _sync_content_width(self, event: tk.Event[tk.Canvas]) -> None:
        self.content_canvas.itemconfigure(self._content_window, width=event.width)
        self.after_idle(self._sync_content_scrollregion)

    def _on_mousewheel(self, event: tk.Event[tk.Misc]) -> None:
        bbox = self.content_canvas.bbox("all")
        if not bbox or bbox[3] <= self.content_canvas.winfo_height():
            return
        if getattr(event, "num", None) == 4:
            delta = -3
        elif getattr(event, "num", None) == 5:
            delta = 3
        else:
            delta = -int(event.delta / 120) if event.delta else 0
        if delta:
            self.content_canvas.yview_scroll(delta, "units")

    def set_busy(self, busy: bool, message: str = "") -> None:
        """Update footer progress state."""

        assert self.progress_controller is not None
        self.progress_controller.set_busy(busy, message)

    def finish_progress(self, on_complete: Callable[[], None]) -> None:
        """Finish progress animation, then run callback."""

        assert self.progress_controller is not None
        self.progress_controller.finish(on_complete)

    def _progress_callback(self) -> Callable[[str], None]:
        self._stage_queue = queue.Queue()
        self._drain_stage_queue()
        stage_queue = self._stage_queue
        return stage_queue.put

    def _drain_stage_queue(self) -> None:
        if self._stage_queue is None:
            return
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        while True:
            try:
                stage = self._stage_queue.get_nowait()
            except queue.Empty:
                break
            self.status_var.set(stage)
        busy = self.progress_controller.animating if self.progress_controller is not None else False
        if busy:
            self.after(75, self._drain_stage_queue)

    def _browse_hosted(self) -> None:
        path = filedialog.askopenfilename(
            title=text.HOSTED_DIALOG,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=self._settings["last_hosted_dir"] or None,
        )
        if not path:
            return
        self.hosted_var.set(path)
        self._settings["last_hosted_dir"] = str(Path(path).parent)
        if not self.outdir_var.get().strip():
            self.outdir_var.set(str(Path(path).parent / "outputs"))
        self._persist_settings()

    def _browse_lastweek(self) -> None:
        path = filedialog.askopenfilename(
            title=text.PRIOR_DIALOG,
            filetypes=[("Excel workbooks", "*.xlsx"), ("All files", "*.*")],
            initialdir=self._settings["last_lastweek_dir"] or None,
        )
        if path:
            self.lastweek_var.set(path)
            self._settings["last_lastweek_dir"] = str(Path(path).parent)
            self._persist_settings()

    def _browse_outdir(self) -> None:
        path = filedialog.askdirectory(
            title=text.OUTPUT_DIALOG,
            initialdir=self.outdir_var.get().strip() or self._settings["output_folder"] or None,
        )
        if path:
            self.outdir_var.set(path)
            self._persist_settings()

    def _start_handoff(self) -> None:
        hosted = self.hosted_var.get().strip()
        lastweek = self.lastweek_var.get().strip()
        if not hosted or not Path(hosted).exists():
            messagebox.showwarning(APP_TITLE, text.HOSTED_REQUIRED)
            return
        if not lastweek or not Path(lastweek).exists():
            messagebox.showwarning(APP_TITLE, text.PRIOR_REQUIRED)
            return
        try:
            self.data.report_date = parse_report_date(self.date_var.get())
        except InputValidationError as exc:
            messagebox.showwarning(APP_TITLE, str(exc))
            return

        output = self.outdir_var.get().strip()
        self.data.output_folder = Path(output) if output else default_output_folder()
        if not output:
            self.outdir_var.set(str(self.data.output_folder))
        self._persist_settings()
        self.data.hosted_path = hosted
        self.data.lastweek_path = lastweek
        self.log.info(
            "Starting handoff | hosted=%s | last_week=%s | output_folder=%s",
            Path(hosted).name,
            Path(lastweek).name,
            self.data.output_folder,
        )
        self._run_handoff()

    def _run_handoff(self) -> None:
        if self._options_open:
            self._toggle_options()
        self._set_handoff_controls(False)
        self.set_busy(True, text.HANDOFF_BUSY)
        progress_callback = self._progress_callback()
        assert self.async_runner is not None
        self.async_runner.run(
            work=lambda: self._run_handoff_work(progress_callback),
            on_success=self._handoff_done,
            on_error=self._handoff_error,
        )

    def _run_handoff_work(self, progress_callback: Callable[[str], None]) -> HandoffWorkResult:
        hosted_path = self.data.hosted_path
        lastweek_path = self.data.lastweek_path
        output_folder = self.data.output_folder
        if hosted_path is None or lastweek_path is None or output_folder is None:
            raise RuntimeError("UID handoff inputs were not initialized")

        handoff = run_uid_handoff(
            hosted_csv_path=hosted_path,
            last_week_xlsx_path=lastweek_path,
            market=self.data.market,
            report_date=self.data.report_date,
            output_folder=output_folder,
            progress_callback=progress_callback,
        )
        clipboard = None
        if handoff.clipboard_uids:
            clipboard = copy_text_to_clipboard("\n".join(handoff.clipboard_uids), use_tk_fallback=False)
        return HandoffWorkResult(handoff=handoff, clipboard=clipboard)

    def _handoff_done(self, result: HandoffWorkResult) -> None:
        handoff = result.handoff
        self.data.market = handoff.market
        self.data.report_date = handoff.report_date
        self.data.missing_uids = list(handoff.clipboard_uids)
        self.data.missing_prior_row_count = handoff.missing_prior_row_count
        self.data.distinct_missing_uid_count = handoff.distinct_missing_uid_count
        self.log.info(
            "Handoff: %s missing prior-workbook rows (%s)",
            self.data.missing_prior_row_count,
            self.data.market,
        )
        if result.clipboard is not None:
            self.data.clipboard_ok = result.clipboard.copied
            self.data.clipboard_message = result.clipboard.message
        else:
            self.data.clipboard_ok = False
            self.data.clipboard_message = text.NO_MISSING_UIDS
        self.finish_progress(self.render_clipboard)

    def _handoff_error(self, exc: Exception) -> None:
        self.set_busy(False)
        self._set_handoff_controls(True)
        if isinstance(exc, MarketInferenceError) and not self.data.market:
            self.log.info("Market could not be inferred; prompting for it", exc_info=exc)
            market = simpledialog.askstring(APP_TITLE, text.MARKET_PROMPT, parent=self)
            if market and market.strip():
                self.data.market = market.strip()
                self._run_handoff()
            return
        self._show_error(exc)

    def _set_handoff_controls(self, enabled: bool) -> None:
        for button in self._handoff_buttons:
            button.set_enabled(enabled)
        if self._options_toggle is not None:
            self._options_toggle.state(["!disabled" if enabled else "disabled"])

    def _copy_again(self) -> None:
        if not self.data.missing_uids:
            return
        result = copy_text_to_clipboard("\n".join(self.data.missing_uids))
        self.data.clipboard_ok = result.copied
        messagebox.showinfo(APP_TITLE, result.message)

    def _browse_reactivated(self) -> None:
        path = filedialog.askopenfilename(
            title=text.REACTIVATED_DIALOG,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=self._settings["last_reactivated_dir"] or None,
        )
        if path:
            self._settings["last_reactivated_dir"] = str(Path(path).parent)
            save_settings(self._settings)
            self._choose_reactivated(Path(path))

    def _choose_reactivated(self, path: Path) -> None:
        if not path.exists():
            messagebox.showwarning(APP_TITLE, f"File not found:\n{path}")
            return
        if path.suffix.lower() != ".csv":
            messagebox.showwarning(APP_TITLE, f"Expected a .csv file, got:\n{path.name}")
            return
        try:
            read_reactivated_players_csv(path)
        except HostedPlayersReportError as exc:
            messagebox.showwarning(APP_TITLE, text.invalid_reactivated(exc))
            return
        self.data.reactivated_csv = path
        self.data.build_attempts = 0
        self.render_build()

    def _start_build(self) -> None:
        create_native_pivot = self.native_pivot_var.get()
        self._persist_settings()
        self.log.info(
            "Starting report build | market=%s | report_date=%s | reactivated_csv=%s | "
            "output_folder=%s | native_pivot=%s",
            self.data.market,
            self.data.report_date,
            self.data.reactivated_csv.name if self.data.reactivated_csv else None,
            self.data.output_folder,
            create_native_pivot,
        )

        hosted_path = self.data.hosted_path
        lastweek_path = self.data.lastweek_path
        output_folder = self.data.output_folder
        if hosted_path is None or lastweek_path is None or output_folder is None:
            self._build_error(RuntimeError("Report inputs were not initialized"))
            return

        self.set_busy(True, text.BUILD_BUSY)
        progress_callback = self._progress_callback()
        assert self.async_runner is not None
        self.async_runner.run(
            work=lambda: run_report(
                hosted_csv_path=hosted_path,
                last_week_xlsx_path=lastweek_path,
                market=self.data.market,
                report_date=self.data.report_date,
                output_folder=output_folder,
                theme_path=self.theme_path,
                reactivated_csv_path=self.data.reactivated_csv,
                overwrite=True,
                create_native_pivot=create_native_pivot,
                require_native_pivot=False,
                progress_callback=progress_callback,
            ),
            on_success=self._build_done,
            on_error=self._build_error,
        )

    def _build_done(self, result: ReportResult) -> None:
        self.data.result = result
        self.log.info("Report built: %s | pivot: %s", result.workbook_path.name, result.pivot_result.message)
        self.finish_progress(self.render_done)

    def _build_error(self, exc: Exception) -> None:
        self.set_busy(False)
        if isinstance(exc, WorkbookLockedError):
            self.log.info(
                "Workbook locked (attempt %s); offering retry",
                self.data.build_attempts + 1,
                exc_info=exc,
            )
            self.data.build_attempts += 1
            if self.data.build_attempts < MAX_BUILD_ATTEMPTS:
                retry = messagebox.askretrycancel(APP_TITLE, text.locked_workbook(exc))
                if retry:
                    self.render_build(None)
                    return
            self.render_build(str(exc))
            return
        self.log.error("Build failed", exc_info=exc)
        self.render_build(str(exc))

    def _diagnostic_id(self) -> str:
        return self.log_session.run_id

    def _show_qa_report(self) -> None:
        result = self.data.result
        if result is None:
            return
        messagebox.showinfo(text.QA_TITLE, text.qa_report(result, self._diagnostic_id()), parent=self)

    def _open_workbook(self) -> None:
        if self.data.result is not None:
            self._safe_open(self.data.result.workbook_path)

    def _safe_open(self, path: Path) -> None:
        try:
            open_in_os(path)
        except Exception as exc:
            messagebox.showwarning(APP_TITLE, text.open_failed(path, exc))

    def _start_over(self) -> None:
        self.hosted_var.set("")
        self.lastweek_var.set("")

        self.data.hosted_path = None
        self.data.lastweek_path = None
        self.data.market = None
        self.data.missing_uids = []
        self.data.missing_prior_row_count = 0
        self.data.distinct_missing_uid_count = 0
        self.data.clipboard_ok = False
        self.data.clipboard_message = ""
        self.data.reactivated_csv = None
        self.data.result = None
        self.data.build_attempts = 0
        self.render_inputs()

    def _show_error(self, exc: Exception) -> None:
        self.log.error("Error shown to user", exc_info=exc)
        messagebox.showerror(APP_TITLE, text.workflow_error(exc, self.log_session.log_path))


def main() -> int:
    """Launch the GUI event loop."""

    _enable_windows_dpi_awareness()
    log_session = configure_logging()
    install_excepthooks(log_session.logger)
    try:
        app = HostedPlayersReportApp()
        app.mainloop()
    except Exception:
        log_session.logger.exception("Fatal error")
        raise
    finally:
        clean_runtime_artifacts(logger=log_session.logger)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
