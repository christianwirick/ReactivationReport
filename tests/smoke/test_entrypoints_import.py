from __future__ import annotations

import unittest

import check_env
import cli
import gui


class EntrypointSmokeTests(unittest.TestCase):
    def test_entrypoints_import(self) -> None:
        self.assertTrue(callable(cli.main))
        self.assertTrue(callable(check_env.main))
        self.assertTrue(callable(gui.main))


if __name__ == "__main__":
    unittest.main()
