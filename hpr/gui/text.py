"""Define GUI messages/dialog text."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hpr.report.run import ReportResult

APP_TITLE = "Hosted Players Report"

HOSTED_REQUIRED = "Choose a valid Hosted Players CSV first."
PRIOR_REQUIRED = "Choose last week's Hosted Players workbook (.xlsx) first."
HANDOFF_BUSY = "Finding reactivated players…"
BUILD_BUSY = "Creating report..."
NO_MISSING_UIDS = "No missing UIDs were found. There is nothing to copy for Tableau."
WORK_IN_PROGRESS = "The report is still running. Keep this window open until it finishes."
HOSTED_DIALOG = "Select the Hosted Players Report"
PRIOR_DIALOG = "Select last week's Hosted Players Report"
OUTPUT_DIALOG = "Select an output folder"
REACTIVATED_DIALOG = "Select the Reactivated Players CSV"

MARKET_PROMPT = (
    "Could not detect the market from Property ID.\n"
    "Enter the market name (e.g. Chicagoland, St. Louis, LBR, Dayton, Toledo):"
)

QA_TITLE = "QA report"


def callback_error(value: BaseException, log_path: Path) -> str:
    """Format an unexpected GUI error."""

    return f"Something went wrong:\n\n{value}\n\nDetails were saved to the log:\n{log_path}"


def invalid_reactivated(error: BaseException) -> str:
    """Invalid CSV warning."""

    return f"That file does not look like a valid Reactivated Players CSV:\n\n{error}"


def locked_workbook(error: BaseException) -> str:
    """Format workbook retry instructions."""

    return f"{error}\n\nClose the workbook in Excel, let OneDrive finish syncing, then choose Retry."


def qa_report(result: ReportResult, diagnostic_id: str) -> str:
    """Format QA summary."""

    details = [
        ("Final workbook", str(result.workbook_path)),
        ("Market", result.market),
        ("Report date", f"{result.report_date:%Y-%m-%d}"),
        ("Reactivated players", str(result.reactivated_player_count)),
        ("Missing prior-workbook rows", str(result.missing_prior_row_count)),
        ("Distinct missing UIDs", str(result.distinct_missing_uid_count)),
        ("Reconciliation", result.reconciliation_status),
        ("Native PivotTables", result.pivot_result.message),
        ("Theme", result.theme_status),
        ("Diagnostic ID", diagnostic_id),
    ]
    return "\n".join(f"{label}: {value}" for label, value in details)


def open_failed(path: Path, error: BaseException) -> str:
    """Format file-open error."""

    return f"Could not open:\n{path}\n\n{error}"


def workflow_error(error: BaseException, log_path: Path) -> str:
    """Format workflow error."""

    return f"{error}\n\nDetails are in the log:\n{log_path}"
