from __future__ import annotations

import io
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
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

    def test_release_builder_loads_outside_repository(self) -> None:
        script_path = Path(build_release.__file__).resolve()
        probe = "import runpy, sys; runpy.run_path(sys.argv[1], run_name='release_builder_probe')"
        with TemporaryDirectory() as temp:
            completed = subprocess.run(
                [sys.executable, "-c", probe, str(script_path)],
                cwd=temp,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
