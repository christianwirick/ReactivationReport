"""Store per-user application settings."""

from __future__ import annotations

import json
import os
import platform
from collections.abc import Mapping
from pathlib import Path
from typing import TypedDict

APP_DIR_NAME = "HostedPlayersReport"


class Settings(TypedDict):
    """Persisted desktop preferences."""

    output_folder: str
    create_pivot: bool
    last_hosted_dir: str
    last_lastweek_dir: str
    last_reactivated_dir: str


DEFAULT_SETTINGS: Settings = {
    "output_folder": "",
    "create_pivot": True,
    "last_hosted_dir": "",
    "last_lastweek_dir": "",
    "last_reactivated_dir": "",
}


def app_data_dir() -> Path:

    override = os.environ.get("HOSTED_PLAYERS_APPDATA")
    if override:
        path = Path(override)
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except OSError:
            pass

    system = platform.system()
    if system == "Windows":
        root = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif system == "Darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")

    path = root / APP_DIR_NAME
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError:
        return Path.home()


def settings_path() -> Path:
    """Return the settings file path."""

    return app_data_dir() / "settings.json"


def default_output_folder() -> Path:
    """Return the default report output folder."""

    downloads = Path.home() / "Downloads"
    return downloads if downloads.exists() else Path.home()


def load_settings(path: Path | None = None) -> Settings:
    """Load valid settings and fill missing values with defaults."""

    path = path or settings_path()
    data = DEFAULT_SETTINGS.copy()
    try:
        if path.exists():
            data = _validated_settings(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    if not data["output_folder"].strip():
        data["output_folder"] = str(default_output_folder())
    return data


def _validated_settings(value: object) -> Settings:
    """Discard unknown keys and values with invalid types."""

    if not isinstance(value, dict):
        return DEFAULT_SETTINGS.copy()

    output_folder = value.get("output_folder")
    create_pivot = value.get("create_pivot")
    last_hosted_dir = value.get("last_hosted_dir")
    last_lastweek_dir = value.get("last_lastweek_dir")
    last_reactivated_dir = value.get("last_reactivated_dir")
    return {
        "output_folder": output_folder if isinstance(output_folder, str) else DEFAULT_SETTINGS["output_folder"],
        "create_pivot": create_pivot if isinstance(create_pivot, bool) else DEFAULT_SETTINGS["create_pivot"],
        "last_hosted_dir": (
            last_hosted_dir if isinstance(last_hosted_dir, str) else DEFAULT_SETTINGS["last_hosted_dir"]
        ),
        "last_lastweek_dir": (
            last_lastweek_dir if isinstance(last_lastweek_dir, str) else DEFAULT_SETTINGS["last_lastweek_dir"]
        ),
        "last_reactivated_dir": (
            last_reactivated_dir if isinstance(last_reactivated_dir, str) else DEFAULT_SETTINGS["last_reactivated_dir"]
        ),
    }


def save_settings(values: Mapping[str, object], path: Path | None = None) -> None:
    """Write known settings keys. Ignore storage failures."""

    path = path or settings_path()
    data = _validated_settings(dict(values))
    try:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError:
        pass
