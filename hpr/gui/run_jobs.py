"""Tk background tasks/progress."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from .widgets import RoundedProgressBar

PENDING_PROGRESS_CAP = 96.0
T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class _Success(Generic[T]):
    value: T


@dataclass(frozen=True, slots=True)
class _Failure:
    error: Exception


class AsyncRunner:
    """Run work outside Tk thread."""

    def __init__(self, owner: tk.Misc, *, poll_ms: int = 50) -> None:
        self.owner = owner
        self.poll_ms = poll_ms

    def run(
        self,
        work: Callable[[], T],
        on_success: Callable[[T], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        result_queue: queue.Queue[_Success[T] | _Failure] = queue.Queue()

        def worker() -> None:
            try:
                result_queue.put(_Success(work()))
            except Exception as exc:
                result_queue.put(_Failure(exc))

        threading.Thread(target=worker, daemon=True).start()
        self._poll(result_queue, on_success, on_error)

    def _poll(
        self,
        result_queue: queue.Queue[_Success[T] | _Failure],
        on_success: Callable[[T], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        try:
            if not self.owner.winfo_exists():
                return
        except tk.TclError:
            return
        try:
            result = result_queue.get_nowait()
        except queue.Empty:
            self.owner.after(self.poll_ms, lambda: self._poll(result_queue, on_success, on_error))
            return
        if isinstance(result, _Failure):
            on_error(result.error)
            return
        on_success(result.value)


class ProgressController:
    """Animate and complete task progress."""

    def __init__(
        self,
        owner: tk.Misc,
        *,
        status_var: tk.StringVar,
        progress: RoundedProgressBar,
        percent_var: tk.StringVar,
        percent_label: tk.Widget,
        tick_ms: int,
        progress_step: float,
        finish_step: float,
    ) -> None:
        self.owner = owner
        self.status_var = status_var
        self.progress = progress
        self.percent_var = percent_var
        self.percent_label = percent_label
        self.tick_ms = tick_ms
        self.progress_step = progress_step
        self.finish_step = finish_step
        self.animating = False
        self._work_done = False
        self._value = 0.0
        self._on_complete: Callable[[], None] | None = None

    def set_busy(self, busy: bool, message: str = "") -> None:
        self.status_var.set(message)
        if busy:
            self._value = 0.0
            self._work_done = False
            self._on_complete = None
            self.progress.set_value(0)
            self.percent_var.set("")
            self.progress.pack(side="right")
            if not self.animating:
                self.animating = True
                self._tick()
            return
        self.animating = False
        self._work_done = False
        self._on_complete = None
        self.progress.pack_forget()
        self.percent_label.pack_forget()

    def finish(self, on_complete: Callable[[], None]) -> None:
        self._work_done = True
        self._on_complete = on_complete
        if not self.animating:
            on_complete()

    def _tick(self) -> None:
        if not self.animating:
            return
        try:
            if not self.owner.winfo_exists():
                self.animating = False
                return
        except tk.TclError:
            self.animating = False
            return
        step = self.finish_step if self._work_done else self.progress_step
        self._value += step
        if self._work_done:
            self._value = min(100.0, self._value)
        elif self._value >= PENDING_PROGRESS_CAP:
            self._value = PENDING_PROGRESS_CAP
        self.progress.set_value(self._value)
        if self._work_done and self._value >= 100.0:
            self.animating = False
            callback = self._on_complete
            self._on_complete = None
            self.progress.pack_forget()
            self.percent_label.pack_forget()
            if callback:
                callback()
            return
        self.owner.after(self.tick_ms, self._tick)
