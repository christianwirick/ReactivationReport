from __future__ import annotations

import subprocess
import sys
import unittest

from hpr._version import __version__


class EnvironmentCheckTests(unittest.TestCase):
    def test_importing_environment_check_does_not_import_runtime_dependencies(self) -> None:
        code = (
            "import sys; "
            "import check_env; "
            "print(check_env.__version__); "
            "raise SystemExit(0 if 'openpyxl' not in sys.modules else 1)"
        )

        completed = subprocess.run(
            [sys.executable, "-c", code],
            check=True,
            text=True,
            capture_output=True,
        )

        self.assertEqual(completed.stdout.strip(), __version__)


if __name__ == "__main__":
    unittest.main()
