from __future__ import annotations

from collections.abc import Iterable


def normalize_uid(value: object) -> str:
    """Return the canonical form of a workbook or Tableau UID."""

    if value is None:
        return ""
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text


def missing_uids(last_week_uids: Iterable[object], current_week_uids: Iterable[object]) -> list[str]:
    """Return last-week UID rows that are absent from the current week."""

    current = {normalize_uid(uid) for uid in current_week_uids if normalize_uid(uid)}
    missing: list[str] = []

    for raw_uid in last_week_uids:
        uid = normalize_uid(raw_uid)

        if not uid:
            continue

        if uid not in current:
            missing.append(uid)

    return missing


def current_uids_from_rows(
    rows: Iterable[dict[str, object]],
) -> list[str]:
    """Extract normalized UniversalPlayerIDs from hosted-player rows."""

    return [normalize_uid(row.get("Universal Player ID")) for row in rows]
