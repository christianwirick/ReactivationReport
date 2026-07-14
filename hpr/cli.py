from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from hpr._version import __version__
from hpr.assets import default_theme_path
from hpr.clean import clean_runtime_artifacts
from hpr.clipboard import ClipboardResult, copy_text_to_clipboard
from hpr.errors import (
    HostedPlayersReportError,
    InputValidationError,
    MarketInferenceError,
    WorkbookLockedError,
)
from hpr.find_downloads import latest_reengagement_csv
from hpr.logs import configure_logging
from hpr.read_tableau import read_reactivated_players_csv
from hpr.report.run import ReportResult, UidHandoffResult, parse_report_date, run_report, run_uid_handoff
from hpr.settings import default_output_folder

LOGGER = logging.getLogger("hpr.cli")


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, run workflow, return process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    log_session = configure_logging(entry_point="cli")
    LOGGER.info(
        "cli_started operation=cli version=%s hosted_csv=%s last_week_xlsx=%s reactivated_csv=%s uid_only=%s",
        __version__,
        Path(args.hosted_csv).name if args.hosted_csv else None,
        Path(args.last_week_xlsx).name if args.last_week_xlsx else None,
        Path(args.reactivated_csv).name if args.reactivated_csv else None,
        args.uid_only,
    )

    try:
        report_date = parse_report_date(args.report_date) if args.report_date else None
        output_folder = Path(args.output_folder) if args.output_folder else default_output_folder()
        theme_path = Path(args.theme) if args.theme else default_theme_path()

        if args.reactivated_csv:
            result = _run_with_lock_retry(args, report_date, output_folder, theme_path, args.reactivated_csv)
            _print_result(result)
            _print_success(result)
            return 0

        handoff = _run_uid_handoff_with_market_prompt(args, report_date, output_folder)
        _print_handoff(handoff)
        if not args.uid_only:
            print()
        copy_result = _copy_uids_for_tableau(handoff.missing_uids)
        _print_tableau_instruction(copy_result.copied, has_uids=bool(handoff.missing_uids))
        if args.uid_only:
            return 0

        print("Download the Reactivated Players CSV, then come back here.")
        reactivated_csv = _choose_reactivated_csv()
        if not reactivated_csv:
            print("Stopped after copying the UIDs. Re-run with --reactivated-csv when ready.")
            return 0

        result = _run_with_lock_retry(
            args,
            report_date,
            output_folder,
            theme_path,
            reactivated_csv=reactivated_csv,
            overwrite=True,
        )
    except HostedPlayersReportError as exc:
        LOGGER.error(
            "cli_failed operation=cli result=expected_error category=%s error_type=%s",
            getattr(exc, "category", "UNKNOWN"),
            type(exc).__name__,
        )
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        LOGGER.exception(
            "cli_failed operation=cli result=unexpected_error error_type=%s",
            type(exc).__name__,
        )
        if log_session.log_unavailable:
            print("ERROR: Unexpected failure. Application logging is unavailable.", file=sys.stderr)
        else:
            print(f"ERROR: Unexpected failure. Details were saved to: {log_session.log_path}", file=sys.stderr)
        return 1
    finally:
        clean_runtime_artifacts(logger=LOGGER)

    _print_result(result)
    _print_success(result)
    return 0


def _run_uid_handoff_with_market_prompt(
    args: argparse.Namespace,
    report_date: date | None,
    output_folder: Path,
) -> UidHandoffResult:
    """Run the UID handoff, prompting for the market if it can't be inferred."""
    while True:
        try:
            return run_uid_handoff(
                hosted_csv_path=args.hosted_csv,
                last_week_xlsx_path=args.last_week_xlsx,
                market=args.market,
                report_date=report_date,
                output_folder=output_folder,
            )
        except MarketInferenceError as exc:
            if args.market:
                raise
            LOGGER.warning(
                "market_prompt_required operation=uid_handoff result=manual_prompt error_type=%s",
                type(exc).__name__,
            )
            print()
            print(f"Could not dynamically calculate the market: {exc}")
            args.market = _prompt_for_market()


def _run_once(
    args: argparse.Namespace,
    report_date: date | None,
    output_folder: Path,
    theme_path: Path,
    reactivated_csv: str | None,
    overwrite: bool,
    create_native_pivot: bool | None = None,
) -> ReportResult:
    return run_report(
        hosted_csv_path=args.hosted_csv,
        last_week_xlsx_path=args.last_week_xlsx,
        market=args.market,
        report_date=report_date,
        output_folder=output_folder,
        theme_path=theme_path,
        reactivated_csv_path=reactivated_csv,
        overwrite=overwrite,
        create_native_pivot=(not args.no_native_pivot) if create_native_pivot is None else create_native_pivot,
        require_native_pivot=args.require_native_pivot,
    )


def _run_with_lock_retry(
    args: argparse.Namespace,
    report_date: date | None,
    output_folder: Path,
    theme_path: Path,
    reactivated_csv: str | None,
    create_native_pivot: bool | None = None,
    overwrite: bool | None = None,
) -> ReportResult:
    """Run the build, retrying after a workbook lock (OneDrive/Excel) up to 3 times.

    Also prompts for the market if it could not be inferred. Re-raises once the
    retry budget is exhausted.
    """
    attempts = 0
    selected_overwrite = args.overwrite if overwrite is None else overwrite
    while True:
        try:
            return _run_once(
                args,
                report_date,
                output_folder,
                theme_path,
                reactivated_csv,
                selected_overwrite,
                create_native_pivot=create_native_pivot,
            )
        except WorkbookLockedError as exc:
            attempts += 1
            if attempts >= 3:
                raise
            LOGGER.warning(
                "workbook_locked_retry operation=report_build result=retry attempt=%s error_type=%s",
                attempts,
                type(exc).__name__,
            )
            print()
            print(exc)
            input("Close the workbook in Excel, let OneDrive finish syncing, then press Enter to retry...")
        except MarketInferenceError as exc:
            if args.market:
                raise
            LOGGER.warning(
                "market_prompt_required operation=report_build result=manual_prompt error_type=%s",
                type(exc).__name__,
            )
            print()
            print(f"Could not dynamically calculate the market: {exc}")
            args.market = _prompt_for_market()


def _print_result(result: ReportResult) -> None:
    """Print the workbook, market, and Excel status for a finished build."""
    print(f"Workbook: {result.workbook_path}")
    print(f"Market: {result.market}")
    print(f"Report date: {result.report_date:%Y-%m-%d}")
    print(f"Theme: {result.theme_status}")
    print(f"Reconciliation: {result.reconciliation_status}")
    print(f"Native pivot: {result.pivot_result.message}")
    print(f"Reactivated Players: {result.reactivated_player_count}")
    print(f"Missing prior-workbook rows: {result.missing_prior_row_count}")
    print(f"Distinct missing UIDs: {result.distinct_missing_uid_count}")


def _print_handoff(result: UidHandoffResult) -> None:
    """Print the market, report date, and missing-UID count after the handoff."""
    print(f"Market: {result.market}")
    print(f"Report date: {result.report_date:%Y-%m-%d}")
    print(f"Missing prior-workbook rows: {result.missing_prior_row_count}")
    print(f"Distinct missing UIDs: {result.distinct_missing_uid_count}")


def _print_success(result: ReportResult) -> None:
    print()
    print("SUCCESS: Hosted Players report is complete.")
    print(f"Final workbook: {result.workbook_path}")


def _copy_uids_for_tableau(uids: Sequence[str]) -> ClipboardResult:
    """Copy the missing UIDs to the clipboard for pasting into Tableau."""
    if not uids:
        print("No missing UIDs were found. There is nothing to copy for Tableau.")
        return ClipboardResult(False, "No UID text was available to copy to clipboard.")
    text = "\n".join(uids)
    result = copy_text_to_clipboard(text)
    print(result.message)
    if not result.copied:
        print("Clipboard unavailable. Copy these UIDs manually:")
        print(text)
    return result


def _print_tableau_instruction(copied: bool, *, has_uids: bool = True) -> None:
    """Tell the user how to get the UIDs into Tableau, depending on the copy result."""
    if not has_uids:
        print("No clipboard handoff is needed for Tableau.")
    elif copied:
        print("UIDs copied to clipboard. Paste them into Tableau.")
    else:
        print("Copy the UIDs listed above and paste them into Tableau.")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the weekly Hosted Players workbook and missing-UID list.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--hosted-csv", required=True, help="Current-week Hosted Players CSV.")
    parser.add_argument("--last-week-xlsx", required=True, help="Last week's Hosted Players workbook.")
    parser.add_argument("--market", help="Optional override for the inferred market.")
    parser.add_argument(
        "--report-date",
        help="Optional report date. Defaults to today. Accepted: M/D/YYYY, M.D.YYYY, or YYYY-MM-DD.",
    )
    parser.add_argument("--output-folder", help="Output folder. Defaults to your Downloads folder.")
    parser.add_argument("--theme", help="Optional Office .thmx theme path.")
    parser.add_argument(
        "--reactivated-csv",
        help="Optional Reactivated Players CSV. If omitted, the CLI prompts after copying the UIDs.",
    )
    parser.add_argument(
        "--uid-only",
        action="store_true",
        help="Stop after copying the missing UIDs to the clipboard (skip the workbook).",
    )
    parser.add_argument("--overwrite", action="store_true", help="Replace existing output files.")
    parser.add_argument(
        "--no-native-pivot",
        action="store_true",
        help="Keep the static Summary fallback and skip Windows Excel automation.",
    )
    parser.add_argument(
        "--require-native-pivot", action="store_true", help="Fail if a native Excel PivotTable cannot be created."
    )
    return parser


def _choose_reactivated_csv() -> str:
    """Prompt for the Reactivated Players CSV (manual path or latest Download).

    Returns the chosen path, or an empty string if the user stops here.
    """
    while True:
        print()
        print("Reactivated Players CSV options:")
        print("  1. Enter the CSV path manually")
        print("  2. Use the most recent Re-Engagement CSV from Downloads")
        choice = input("Type 1 or 2 (blank to stop here): ").strip()
        if not choice:
            return ""
        if choice == "1":
            path = _prompt_for_reactivated_csv()
            if not path:
                return ""
            if _validate_reactivated_csv_path(path):
                return path
            continue
        if choice == "2":
            latest_path = latest_reengagement_csv()
            if not latest_path:
                print("No Re-Engagement CSV was found in your Downloads folder.")
                continue
            print(f"Using latest downloaded Reactivated Players CSV: {latest_path}")
            if _validate_reactivated_csv_path(str(latest_path)):
                return str(latest_path)
            continue
        print("Please type 1, 2, or press Enter to stop.")


def _prompt_for_reactivated_csv() -> str:
    raw = input("Reactivated Players CSV path (blank to stop here): ").strip()
    return raw.strip('"').strip("'") if raw else ""


def _validate_reactivated_csv_path(path: str) -> bool:
    """Return True if ``path`` is an existing, readable Reactivated Players CSV."""
    csv_path = Path(path)
    if not csv_path.exists():
        print(f"File not found: {csv_path}")
        return False
    if csv_path.suffix.lower() != ".csv":
        print(f"Expected a .csv file, got: {csv_path}")
        return False
    try:
        read_reactivated_players_csv(csv_path)
    except InputValidationError as exc:
        print(f"That file does not look like a valid Reactivated Players CSV: {exc}")
        return False
    return True


def _prompt_for_market() -> str:
    while True:
        raw = input("Enter market name (for example Chicagoland, St. Louis, LBR, Dayton, Toledo): ").strip()
        market = raw.strip('"').strip("'")
        if market:
            return market
        print("Market name is required.")


if __name__ == "__main__":
    raise SystemExit(main())
