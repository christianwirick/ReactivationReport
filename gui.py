"""Thin launcher for the Hosted Players Report GUI."""

from __future__ import annotations

from hpr.gui.app import APP_VERSION, main

__all__ = ["APP_VERSION", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
