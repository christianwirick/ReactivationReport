from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from hpr.settings import default_output_folder, load_settings


class SettingsTests(unittest.TestCase):
    def test_invalid_known_values_fall_back_by_field(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "settings.json"
            path.write_text(
                json.dumps(
                    {
                        "output_folder": ["bad"],
                        "create_pivot": None,
                        "last_hosted_dir": 7,
                        "last_lastweek_dir": "C:/valid",
                        "last_reactivated_dir": False,
                    }
                ),
                encoding="utf-8",
            )

            settings = load_settings(path)

        self.assertEqual(settings["output_folder"], str(default_output_folder()))
        self.assertTrue(settings["create_pivot"])
        self.assertEqual(settings["last_hosted_dir"], "")
        self.assertEqual(settings["last_lastweek_dir"], "C:/valid")
        self.assertEqual(settings["last_reactivated_dir"], "")


if __name__ == "__main__":
    unittest.main()
