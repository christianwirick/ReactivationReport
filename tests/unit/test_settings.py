from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from hpr.settings import default_output_folder, load_settings, save_settings


class SettingsTests(unittest.TestCase):
    def test_invalid_known_values_fall_back_by_field(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "settings.json"
            path.write_text(
                json.dumps(
                    {
                        "output_folder": ["bad"],
                        "last_hosted_dir": 7,
                        "last_lastweek_dir": "C:/valid",
                        "last_reactivated_dir": False,
                    }
                ),
                encoding="utf-8",
            )

            settings = load_settings(path)

        self.assertEqual(settings["output_folder"], str(default_output_folder()))
        self.assertEqual(settings["last_hosted_dir"], "")
        self.assertEqual(settings["last_lastweek_dir"], "C:/valid")
        self.assertEqual(settings["last_reactivated_dir"], "")

    def test_legacy_create_pivot_key_is_ignored_and_not_saved(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "settings.json"
            path.write_text(
                json.dumps(
                    {
                        "output_folder": "C:/Reports",
                        "create_pivot": False,
                        "last_hosted_dir": "C:/Hosted",
                        "last_lastweek_dir": "C:/Prior",
                        "last_reactivated_dir": "C:/Reactivated",
                    }
                ),
                encoding="utf-8",
            )

            settings = load_settings(path)
            save_settings({**settings, "create_pivot": False}, path)
            saved = json.loads(path.read_text(encoding="utf-8"))

        self.assertNotIn("create_pivot", settings)
        self.assertNotIn("create_pivot", saved)
        self.assertEqual(settings["output_folder"], "C:/Reports")


if __name__ == "__main__":
    unittest.main()
