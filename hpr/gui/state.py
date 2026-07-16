"""Store state shared across wizard steps."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hpr.clipboard import ClipboardResult
    from hpr.report.run import ReportResult, UidHandoffResult


@dataclass(frozen=True)
class HandoffWorkResult:
    """UID handoff data with its clipboard status."""

    handoff: UidHandoffResult
    clipboard: ClipboardResult | None


@dataclass
class GuiState:
    """Preserve wizard inputs and results across screens."""

    hosted_path: str | None = None
    lastweek_path: str | None = None
    market: str | None = None
    report_date: date | None = None
    output_folder: Path | None = None
    missing_uids: list[str] = field(default_factory=list)
    missing_prior_row_count: int = 0
    distinct_missing_uid_count: int = 0
    clipboard_ok: bool = False
    reactivated_csv: Path | None = None
    result: ReportResult | None = None
    build_attempts: int = 0
