"""Remove repository and runtime cache files."""

from __future__ import annotations

import logging
import shutil
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_JUNK_DIR_NAMES = {"__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
RUNTIME_JUNK_FILE_NAMES = {".DS_Store"}
RUNTIME_JUNK_SUFFIXES = {".pyc", ".pyo"}


def clean_runtime_artifacts(root: Path | None = None, logger: logging.Logger | None = None) -> int:
    """Remove cache files under the application tree."""

    root = root or ROOT
    removed = 0
    for path in sorted(_iter_runtime_junk(root), key=lambda item: len(item.parts), reverse=True):
        try:
            if not path.exists():
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            removed += 1
        except OSError:
            if logger is not None:
                logger.debug("runtime_clean_failed target_path=%s", path, exc_info=True)
    if removed and logger is not None:
        logger.info("runtime_clean_complete operation=clean removed=%s", removed)
    return removed


def _iter_runtime_junk(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if any(parent.name in RUNTIME_JUNK_DIR_NAMES for parent in path.parents):
            continue
        if (path.name in RUNTIME_JUNK_DIR_NAMES and path.is_dir()) or (
            path.is_file() and (path.name in RUNTIME_JUNK_FILE_NAMES or path.suffix in RUNTIME_JUNK_SUFFIXES)
        ):
            yield path


def main() -> int:
    """Clean the repository and report the number of removed paths."""

    removed = clean_runtime_artifacts()
    if removed:
        print(f"Removed {removed} cache artifact(s).")
    else:
        print("No cache artifacts found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
