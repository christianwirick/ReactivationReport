"""Locate latest Reactivated Players export."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def latest_reengagement_csv(
    downloads_dir: str | Path | None = None,
) -> Path | None:
    """Return the newest re-engagement CSV in the downloads directory."""

    downloads = Path(downloads_dir) if downloads_dir else Path.home() / "Downloads"

    if not downloads.exists():
        logger.info(
            "latest_reengagement_lookup operation=download_lookup result=no_downloads_dir target=%s",
            downloads.name,
        )
        return None

    candidates: list[tuple[float, str, Path]] = []

    for path in downloads.iterdir():
        if not _is_reengagement_candidate(path):
            continue

        try:
            modified = path.stat().st_mtime
        except OSError as exc:
            logger.warning(
                "latest_reengagement_lookup "
                "operation=download_lookup "
                "result=skipped_inaccessible "
                "source_file=%s "
                "error_type=%s",
                path.name,
                type(exc).__name__,
            )
            continue

        candidates.append((modified, path.name.lower(), path))

    if not candidates:
        logger.info("latest_reengagement_lookup operation=download_lookup result=no_match")
        return None

    selected = max(
        candidates,
        key=lambda item: (item[0], item[1]),
    )[2]

    logger.info(
        "latest_reengagement_lookup operation=download_lookup result=selected source_file=%s",
        selected.name,
    )

    return selected


def _is_reengagement_candidate(path: Path) -> bool:
    name = path.name
    lowered = name.lower()
    return (
        path.is_file()
        and path.suffix.lower() == ".csv"
        and lowered.startswith("re-engagement")
        and not name.startswith("~$")
        and not name.startswith(".")
    )
