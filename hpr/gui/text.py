"""Define GUI messages/dialog text."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hpr.report.run import ReportResult

# Shared copy
APP_TITLE = "Hosted Players Report"
BACK_BUTTON = "←  Back"
CONTINUE_BUTTON = "Continue"
CONTINUE_ARROW_BUTTON = "Continue  →"
CSV_FILES_LABEL = "CSV files"
EXCEL_WORKBOOKS_LABEL = "Excel workbooks"
ALL_FILES_LABEL = "All files"
WORK_IN_PROGRESS = "The report is still running. Keep this window open until it finishes."
MARKET_PROMPT = (
    "Could not detect the market from Property ID.\n"
    "Enter the market name (e.g. Chicagoland, St. Louis, LBR, Dayton, Toledo):"
)

# Step 1: files and settings
ADD_REPORTS_HEADING = "Add files"
HOSTED_PLAY_REPORT_LABEL = "90 day play report"
HOSTED_PLAY_REPORT_HINT = "The Tableau .csv export"
LAST_WEEK_WORKBOOK_LABEL = "Last week's workbook"
LAST_WEEK_WORKBOOK_HINT = "The finished .xlsx from last run"
SETTINGS_HEADING = "Settings"
SETTINGS_SUBTITLE = "Optional report settings."
REPORT_DATE_LABEL = "Report date"
OUTPUT_FOLDER_LABEL = "Output folder"
QA_OPTION = "QA mode"
HOSTED_REQUIRED = "Choose a valid Hosted Players CSV first."
PRIOR_REQUIRED = "Choose last week's Hosted Players workbook (.xlsx) first."
HANDOFF_BUSY = "Finding reactivated players…"
HOSTED_DIALOG = "Select the Hosted Players Report"
PRIOR_DIALOG = "Select last week's Hosted Players Report"
OUTPUT_DIALOG = "Select an output folder"

# Step 2: clipboard handoff
NO_MISSING_UIDS_HEADING = "No missing UIDs found"
CLIPBOARD_FAILURE_HEADING = "Couldn't copy to your clipboard"
NO_CLIPBOARD_HANDOFF = "No Tableau clipboard handoff is needed for this run."
PASTE_UIDS_INSTRUCTION = "Paste them into Tableau."
DOWNLOAD_CSV_INSTRUCTION = "Download the CSV."
RETURN_CONTINUE_INSTRUCTION = "Return here and continue."
ZERO_MISSING_INSTRUCTIONS = "1.   Download the CSV.\n2.   Click continue."
TABLEAU_HANDOFF_INSTRUCTIONS = "1.   Paste them into Tableau.\n2.   Download the CSV.\n3.   Return here and continue."
LOST_UIDS_CAPTION = "NEED ANOTHER COPY?"
COPY_BUTTON = "Copy"
COPY_UIDS_BUTTON = "Copy UIDs"

# Step 3: reactivated export
SELECT_EXPORT_HEADING = "Select Tableau export"
USE_RECENT_FILE_BUTTON = "Select"
NO_RECENT_DOWNLOAD = "No recent Re-Engagement CSV in your Downloads folder."
REACTIVATED_DIALOG = "Select the Reactivated Players CSV"

# Step 4: build and completion
BUILD_BUSY = "Creating report..."
BUILD_WAIT_SUBTITLE = "This may take a moment."
BUILD_FAILURE_HEADING = "Couldn't build the report"
CHOOSE_DIFFERENT_FILE_BUTTON = "←  Choose a different file"
VIEW_LOG_BUTTON = "View log"
TRY_AGAIN_BUTTON = "Try again"
SUCCESS_HEADING = "✓  Success"
FINAL_WORKBOOK_LABEL = "Final workbook"
MARKET_LABEL = "Market"
REACTIVATED_PLAYERS_LABEL = "Reactivated players"
QA_TITLE = "QA report"
OPEN_WORKBOOK_BUTTON = "Open workbook"
MISSING_PRIOR_ROWS_LABEL = "Missing prior-workbook rows"
DISTINCT_MISSING_UIDS_LABEL = "Distinct missing UIDs"
RECONCILIATION_LABEL = "Reconciliation"
NATIVE_PIVOTS_LABEL = "Native PivotTables"
THEME_LABEL = "Theme"
DIAGNOSTIC_ID_LABEL = "Diagnostic ID"


def window_title(version: str) -> str:
    """Format the application window title."""

    return f"{APP_TITLE}  v{version}"


def step_label(step: int, total: int) -> str:
    """Format the wizard step label."""

    return f"Step {step} of {total}"


def copied_uids_heading(count: int) -> str:
    """Format the successful clipboard heading."""

    return f"✓  {count} UIDs copied to your clipboard"


def recent_download_modified(timestamp: float) -> str:
    """Format a recent download timestamp."""

    modified = datetime.fromtimestamp(timestamp)
    day = "today" if modified.date() == datetime.now().date() else modified.strftime("%b %d, %Y").replace(" 0", " ")
    time = modified.strftime("%I:%M %p").lstrip("0")
    return f"Downloads · {day} at {time}"


def file_not_found(path: Path) -> str:
    """Format a missing-file warning."""

    return f"File not found:\n{path}"


def wrong_file_extension(path: Path) -> str:
    """Format a wrong-extension warning."""

    return f"Expected a .csv file, got:\n{path.name}"


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
        (FINAL_WORKBOOK_LABEL, str(result.workbook_path)),
        (MARKET_LABEL, result.market),
        (REPORT_DATE_LABEL, f"{result.report_date:%Y-%m-%d}"),
        (REACTIVATED_PLAYERS_LABEL, str(result.reactivated_player_count)),
        (MISSING_PRIOR_ROWS_LABEL, str(result.missing_prior_row_count)),
        (DISTINCT_MISSING_UIDS_LABEL, str(result.distinct_missing_uid_count)),
        (RECONCILIATION_LABEL, result.reconciliation_status),
        (NATIVE_PIVOTS_LABEL, result.pivot_result.message),
        (THEME_LABEL, result.theme_status),
        (DIAGNOSTIC_ID_LABEL, diagnostic_id),
    ]
    return "\n".join(f"{label}: {value}" for label, value in details)


def open_failed(path: Path, error: BaseException) -> str:
    """Format file-open error."""

    return f"Could not open:\n{path}\n\n{error}"


def workflow_error(error: BaseException, log_path: Path) -> str:
    """Format workflow error."""

    return f"{error}\n\nDetails are in the log:\n{log_path}"
