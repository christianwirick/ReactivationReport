from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import cli
import gui
import hpr.check_env as check_env
import tools.build_release as build_release
from hpr import __version__


class VersionTests(unittest.TestCase):
    def test_gui_uses_package_version(self) -> None:
        self.assertEqual(gui.APP_VERSION, __version__)

    def test_cli_version_uses_package_version(self) -> None:
        with self.assertRaises(SystemExit) as caught, redirect_stdout(io.StringIO()) as stdout:
            cli.main(["--version"])

        self.assertEqual(caught.exception.code, 0)
        self.assertIn(__version__, stdout.getvalue())

    def test_environment_check_output_uses_package_version(self) -> None:
        with (
            patch("hpr.check_env.select_python", return_value=(None, [])),
            patch("hpr.check_env.build_checks", return_value=[]),
            redirect_stdout(io.StringIO()) as stdout,
        ):
            exit_code = check_env.main([])

        self.assertEqual(exit_code, 0)
        self.assertIn(f"Version: {__version__}", stdout.getvalue())

    def test_environment_check_json_uses_package_version(self) -> None:
        with (
            patch("hpr.check_env.select_python", return_value=(None, [])),
            patch("hpr.check_env.build_checks", return_value=[]),
            redirect_stdout(io.StringIO()) as stdout,
        ):
            exit_code = check_env.main(["--json"])

        self.assertEqual(exit_code, 0)
        self.assertIn(f'"version": "{__version__}"', stdout.getvalue())

    def test_release_builder_uses_package_version(self) -> None:
        self.assertEqual(build_release.read_version(), __version__)


if __name__ == "__main__":
    unittest.main()
