"""Read Tableau exports."""

from __future__ import annotations

import csv
import logging
from collections.abc import Sequence
from datetime import date, datetime
from pathlib import Path

from .errors import InputValidationError
from .schema import DATE_COLUMNS, HOSTED_COLUMNS, REACTIVATED_COLUMNS, TEXT_COLUMNS

logger = logging.getLogger(__name__)


def read_hosted_players_csv(path: str | Path) -> list[dict[str, object]]:
    """Read the weekly Hosted Players Tableau export."""

    return read_tableau_tsv(path, HOSTED_COLUMNS)


def read_reactivated_players_csv(path: str | Path) -> list[dict[str, object]]:
    """Read the manually exported Reactivated Players Tableau CSV."""

    return read_tableau_tsv(path, REACTIVATED_COLUMNS)


def read_tableau_tsv(path: str | Path, required_columns: list[str]) -> list[dict[str, object]]:
    """Read a UTF-16, tab-delimited Tableau export into canonical columns."""

    csv_path = Path(path)
    if not csv_path.exists():
        raise InputValidationError(f"File does not exist: {csv_path}")

    try:
        logger.info(
            "input_file_opened operation=csv_parse source_file=%s",
            csv_path.name,
        )
        with csv_path.open("r", encoding="utf-16", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if not reader.fieldnames:
                raise InputValidationError(f"CSV has no header row: {csv_path.name}")
            column_map = _map_required_columns(reader.fieldnames, required_columns, csv_path.name)
            rows = []
            for raw_row in reader:
                source_row_number = reader.line_num
                row = {}
                for required, source in column_map.items():
                    raw_value = raw_row.get(source, "")
                    try:
                        row[required] = _coerce_value(required, raw_value)
                    except InputValidationError as exc:
                        expected = _expected_format(required)
                        raise InputValidationError(
                            f"{csv_path.name} row {source_row_number}, column '{required}' "
                            f"has invalid value {_sanitize_value(raw_value)}; expected {expected}."
                        ) from exc
                if any(value not in ("", None) for value in row.values()):
                    rows.append(row)
    except UnicodeError as exc:
        raise InputValidationError(f"{csv_path.name} could not be read as a UTF-16 Tableau export.") from exc
    except csv.Error as exc:
        raise InputValidationError(f"{csv_path.name} is not a valid tab-delimited CSV.") from exc
    except OSError as exc:
        raise InputValidationError(f"Could not read CSV file: {csv_path}. {exc}") from exc

    if not rows:
        raise InputValidationError(f"CSV contains no data rows: {csv_path.name}")
    logger.info(
        "rows_parsed operation=csv_parse source_file=%s row_count=%s result=success",
        csv_path.name,
        len(rows),
    )
    return rows


def _map_required_columns(actual_columns: Sequence[str], required_columns: list[str], file_name: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    actual_by_stripped: dict[str, str] = {}

    for column in actual_columns:
        actual_by_stripped.setdefault(column.strip(), column)

    missing = []
    for required in required_columns:
        if required in actual_columns:
            mapping[required] = required
        elif required.strip() in actual_by_stripped:
            mapping[required] = actual_by_stripped[required.strip()]
        else:
            missing.append(required)

    if missing:
        missing_text = ", ".join(missing)
        detected_text = ", ".join(actual_columns)
        raise InputValidationError(
            f"{file_name} is missing required columns: {missing_text}. detected columns: {detected_text}"
        )
    return mapping


def _coerce_value(column: str, value: object) -> object:
    if value is None:
        return None

    if column in TEXT_COLUMNS:
        return str(value).strip()

    if column in DATE_COLUMNS:
        return _parse_date(value)

    return _parse_number(value)


def _parse_date(value: object) -> date | None:
    if value in ("", None):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text = str(value).strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise InputValidationError(f"Could not parse date value: {text}")


def _parse_number(value: object) -> int | float | None:
    if value in ("", None):
        return None
    if isinstance(value, (int, float)):
        return value

    text = str(value).strip()
    if not text:
        return None

    negative = text.startswith("(") and text.endswith(")")
    cleaned = text.strip("()").replace(",", "").replace("$", "")
    if cleaned == "":
        return None

    try:
        number: int | float = float(cleaned) if "." in cleaned else int(cleaned)
    except ValueError as exc:
        raise InputValidationError(f"Could not parse numeric value: {text}") from exc

    return -number if negative else number


def _expected_format(column: str) -> str:
    if column in DATE_COLUMNS:
        return "M/D/YYYY, YYYY-MM-DD, or YYYY-MM-DD HH:MM:SS"
    if column in TEXT_COLUMNS:
        return "text"
    return "a number"


def _sanitize_value(value: object) -> str:
    if value is None:
        return "<null>"
    text = str(value)
    text = text.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")
    if len(text) > 80:
        text = text[:77] + "..."
    return repr(text)
