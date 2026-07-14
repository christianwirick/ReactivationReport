"""Configure application-boundary logging."""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from uuid import uuid4

from .settings import APP_DIR_NAME, app_data_dir

LOGGER_NAME = "hpr"


@dataclass(frozen=True, slots=True)
class LogSession:
    """Configured logger and its run metadata."""

    logger: logging.Logger
    log_path: Path
    run_id: str
    log_unavailable: bool


_active_session: LogSession | None = None


def configure_logging(
    *,
    entry_point: str = "gui",
    log_dir: Path | None = None,
    level: str | int | None = None,
    run_id: str | None = None,
    force: bool = False,
) -> LogSession:
    """Configure application logging and return the active session."""
    global _active_session

    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers and not force and _active_session is not None:
        return _active_session

    for handler in list(logger.handlers):
        logger.removeHandler(handler)

        try:
            handler.close()
        except Exception:
            pass

    selected_level = _resolve_log_level(level)
    selected_log_dir = log_dir or app_data_dir()

    try:
        selected_log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        selected_log_dir = app_data_dir()

    log_path = selected_log_dir / "app.log"
    context_filter = _RunContextFilter(
        entry_point=entry_point,
        run_id=run_id or uuid4().hex[:12],
    )

    try:
        handler = _create_log_handler(
            log_path,
            selected_level,
            context_filter,
        )
        logger.addHandler(handler)
        logger.setLevel(selected_level)
        logger.propagate = False

        _active_session = LogSession(
            logger,
            log_path,
            context_filter.run_id,
            False,
        )

    except Exception:
        fallback_path = Path(tempfile.gettempdir()) / APP_DIR_NAME / "app.log"

        try:
            fallback_path.parent.mkdir(parents=True, exist_ok=True)

            handler = _create_log_handler(fallback_path, selected_level, context_filter)
            logger.addHandler(handler)
            logger.setLevel(selected_level)
            logger.propagate = False

            _active_session = LogSession(
                logger,
                fallback_path,
                context_filter.run_id,
                False,
            )
            logger.warning(
                "logging_fallback_used operation=logging_setup result=temp_log target_path=%s",
                fallback_path,
            )
            return _active_session
        except Exception:
            pass

        logger.addHandler(logging.NullHandler())
        logger.setLevel(selected_level)
        logger.propagate = False

        _active_session = LogSession(logger, log_path, context_filter.run_id, True)
        print(
            "WARNING: Hosted Players Report logging is unavailable; diagnostics will be limited.",
            file=sys.stderr,
        )

    return _active_session


def _create_log_handler(
    log_path: Path,
    selected_level: int,
    context_filter: logging.Filter,
) -> logging.Handler:
    handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=512_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setLevel(selected_level)
    handler.addFilter(context_filter)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s  %(levelname)-7s  %(name)s:%(lineno)d  "
            "[pid=%(process)d run_id=%(run_id)s entry_point=%(entry_point)s]  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    return handler


def _resolve_log_level(level: str | int | None) -> int:
    if isinstance(level, int):
        return level

    text = str(level or os.environ.get("HOSTED_PLAYERS_LOG_LEVEL") or "INFO").upper()
    return getattr(logging, text, logging.INFO)


class _RunContextFilter(logging.Filter):
    def __init__(self, *, entry_point: str, run_id: str) -> None:
        super().__init__()
        self.entry_point = entry_point
        self.run_id = run_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.entry_point = self.entry_point
        record.run_id = self.run_id
        return True


def install_excepthooks(logger: logging.Logger) -> None:
    """Route uncaught main-thread and worker-thread errors to the logger."""

    def main_hook(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: TracebackType | None,
    ) -> None:
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))

    def thread_hook(args: threading.ExceptHookArgs) -> None:
        exc_value = args.exc_value or RuntimeError("Thread failed without an exception value")
        logger.critical(
            "Uncaught exception in thread %s",
            getattr(args.thread, "name", "?"),
            exc_info=(args.exc_type, exc_value, args.exc_traceback),
        )

    sys.excepthook = main_hook
    threading.excepthook = thread_hook
