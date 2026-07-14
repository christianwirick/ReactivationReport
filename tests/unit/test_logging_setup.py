from __future__ import annotations

import io
import logging
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from hpr.logs import configure_logging


class LoggingSetupTests(unittest.TestCase):
    def test_logging_unavailable_is_signaled_when_primary_and_temp_handlers_fail(self) -> None:
        with (
            TemporaryDirectory() as temp,
            patch("hpr.logs.logging.handlers.RotatingFileHandler", side_effect=OSError("no log")),
            redirect_stderr(io.StringIO()) as stderr,
        ):
            session = configure_logging(log_dir=Path(temp), force=True)

        self.assertIsInstance(session.logger.handlers[0], logging.NullHandler)
        self.assertTrue(session.log_unavailable)
        self.assertIn("logging is unavailable", stderr.getvalue())

    def test_repeated_setup_returns_the_active_session(self) -> None:
        with TemporaryDirectory() as temp:
            first = configure_logging(log_dir=Path(temp), force=True)
            second = configure_logging(log_dir=Path(temp))

        self.assertIs(second, first)
        self.assertIs(second.logger, first.logger)
        self.assertEqual(second.run_id, first.run_id)
        self.assertEqual(len(second.logger.handlers), 1)


if __name__ == "__main__":
    unittest.main()
