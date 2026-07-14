from __future__ import annotations

import argparse
import io
import logging
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, sentinel

import hpr.cli as cli
from hpr.logs import LogSession, configure_logging


class CliTests(unittest.TestCase):
    def test_lock_retry_passes_overwrite_without_mutating_arguments(self) -> None:
        args = argparse.Namespace(overwrite=False)
        output_folder = Path("output")
        theme_path = Path("theme.thmx")

        with patch("hpr.cli._run_once", return_value=sentinel.result) as run_once:
            result = cli._run_with_lock_retry(
                args,
                None,
                output_folder,
                theme_path,
                "reactivated.csv",
                overwrite=True,
            )

        self.assertIs(result, sentinel.result)
        self.assertFalse(args.overwrite)
        run_once.assert_called_once_with(
            args,
            None,
            output_folder,
            theme_path,
            "reactivated.csv",
            True,
            create_native_pivot=None,
        )

    def test_known_report_error_returns_stable_exit_code_two(self) -> None:
        argv = [
            "--hosted-csv",
            "hosted.csv",
            "--last-week-xlsx",
            "prior.xlsx",
            "--reactivated-csv",
            "reactivated.csv",
        ]
        from hpr.errors import InputValidationError

        logger = logging.getLogger("test.cli")
        log_session = LogSession(logger, Path("app.log"), "test-run", False)
        with (
            patch("hpr.cli.configure_logging", return_value=log_session),
            patch(
                "hpr.cli._run_with_lock_retry",
                side_effect=InputValidationError("bad input"),
            ),
            patch("sys.stderr", new_callable=io.StringIO) as stderr,
        ):
            exit_code = cli.main(argv)

        self.assertEqual(exit_code, 2)
        self.assertIn("ERROR: bad input", stderr.getvalue())

    def test_unexpected_cli_exception_logs_traceback_and_returns_one(self) -> None:
        argv = [
            "--hosted-csv",
            "hosted.csv",
            "--last-week-xlsx",
            "prior.xlsx",
            "--reactivated-csv",
            "reactivated.csv",
        ]
        with TemporaryDirectory() as temp:
            log_dir = Path(temp)
            log_session = configure_logging(entry_point="cli", log_dir=log_dir, level="DEBUG", force=True)
            with (
                patch("hpr.cli.configure_logging", return_value=log_session),
                patch("hpr.cli._run_with_lock_retry", side_effect=RuntimeError("boom")),
                patch("sys.stderr", new_callable=io.StringIO) as stderr,
            ):
                exit_code = cli.main(argv)

            log_text = (log_dir / "app.log").read_text(encoding="utf-8")

        self.assertEqual(exit_code, 1)
        self.assertIn("ERROR: Unexpected failure", stderr.getvalue())
        self.assertIn("RuntimeError: boom", log_text)
        self.assertIn("Traceback", log_text)


class PythonResolverTests(unittest.TestCase):
    def test_candidate_paths_include_explicit_active_venv_conda_and_path_commands(self) -> None:
        from check_env import collect_python_candidates

        env = {
            "HOSTED_PLAYERS_PYTHON": r"C:\Python With Spaces\python.exe",
            "VIRTUAL_ENV": r"C:\venv",
            "CONDA_PREFIX": r"C:\conda",
            "LOCALAPPDATA": r"C:\Users\me\AppData\Local",
        }

        def fake_which(command: str):
            return {"py": r"C:\Windows\py.exe", "python": r"C:\Python311\python.exe"}.get(command)

        candidates = collect_python_candidates(env=env, which=fake_which)
        sources = [candidate.source for candidate in candidates]

        self.assertIn("explicit HOSTED_PLAYERS_PYTHON", sources)
        self.assertIn("active virtual environment", sources)
        self.assertIn("active Conda environment", sources)
        self.assertIn("py launcher", sources)
        self.assertIn("python on PATH", sources)


if __name__ == "__main__":
    unittest.main()
