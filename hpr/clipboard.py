"""Provides clipboard support for the Tableau UID handoff."""

from __future__ import annotations

import logging
import platform
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClipboardResult:
    copied: bool
    message: str


def copy_text_to_clipboard(text: str, *, use_tk_fallback: bool = True) -> ClipboardResult:
    """Copy text to the OS clipboard."""

    if not text:
        return ClipboardResult(False, "No UID text was available to copy to clipboard.")

    system = platform.system()
    commands = []
    if system == "Windows":
        commands = [["clip"]]
    elif system == "Darwin":
        commands = [["pbcopy"]]

    failures: list[str] = []
    for command in commands:
        try:
            subprocess.run(command, input=text, text=True, check=True)
            logger.info(
                "clipboard_copy operation=clipboard result=success strategy=%s",
                command[0],
            )
            return ClipboardResult(True, "UIDs copied to clipboard.")
        except (OSError, subprocess.CalledProcessError) as exc:
            failures.append(f"{command[0]} failed: {exc}")
            logger.warning(
                "clipboard_copy operation=clipboard result=strategy_failed strategy=%s error_type=%s",
                command[0],
                type(exc).__name__,
            )

    if not use_tk_fallback:
        logger.warning("clipboard_copy operation=clipboard result=failed strategy=platform_only")
        if not failures:
            failures.append("no platform clipboard command was available")
        return ClipboardResult(False, "Could not copy UIDs to clipboard: " + "; ".join(failures))

    tk_result = _copy_with_tkinter(text)
    if tk_result.copied:
        logger.info("clipboard_copy operation=clipboard result=success strategy=tkinter")
        return tk_result
    failures.append(tk_result.message)
    logger.warning("clipboard_copy operation=clipboard result=failed strategy=all")
    return ClipboardResult(False, "Could not copy UIDs to clipboard: " + "; ".join(failures))


def _copy_with_tkinter(text: str) -> ClipboardResult:
    root = None
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
    except Exception as exc:
        return ClipboardResult(False, f"Could not copy UIDs to clipboard: {exc}")
    finally:
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass
    return ClipboardResult(True, "UIDs copied to clipboard.")
