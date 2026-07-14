"""Locate files bundled with the application."""

from __future__ import annotations

from pathlib import Path


def resource_path(name: str) -> Path:
    """Return the path to a bundled asset."""

    return Path(__file__).resolve().parent / "assets" / name


def default_theme_path() -> Path:
    """Return the bundled Excel theme path."""

    return resource_path("theme.thmx")


def default_logo_path() -> Path | None:
    """Return the bundled logo path when it exists."""

    path = resource_path("logo.png")
    return path if path.exists() else None
