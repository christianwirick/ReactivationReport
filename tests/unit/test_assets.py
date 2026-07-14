from __future__ import annotations

import unittest

from hpr.assets import default_logo_path, default_theme_path


class AssetTests(unittest.TestCase):
    def test_bundled_asset_paths_resolve_inside_the_package(self) -> None:
        logo_path = default_logo_path()

        self.assertIsNotNone(logo_path)
        assert logo_path is not None
        self.assertTrue(logo_path.is_file())
        self.assertEqual(logo_path.parent.name, "assets")
        self.assertTrue(default_theme_path().is_file())


if __name__ == "__main__":
    unittest.main()
