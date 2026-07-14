from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from hpr.excel.build_pivots import PivotAutomationResult
from hpr.report.run import run_report, run_uid_handoff
from tests.fixtures.report_data import (
    hosted_row,
    reactivated_row,
    write_hosted_csv,
    write_prior_workbook,
    write_reactivated_csv,
)


class PipelineProgressTests(unittest.TestCase):
    def test_run_report_emits_ordered_stage_names(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            stages: list[str] = []
            hosted_csv = write_hosted_csv(root / "hosted.csv", [hosted_row()])
            prior = write_prior_workbook(root / "prior.xlsx", "Baton Rouge", ["999"])
            reactivated_csv = write_reactivated_csv(
                root / "reactivated.csv",
                [reactivated_row(**{"Universal Player ID": "999"})],
            )
            pivot_result = PivotAutomationResult(False, "Skipped native PivotTable: forced test fallback.")

            with patch("hpr.report.run.create_native_summary_pivot", return_value=pivot_result):
                run_report(
                    hosted_csv_path=hosted_csv,
                    last_week_xlsx_path=prior,
                    market="Baton Rouge",
                    report_date=date(2026, 6, 1),
                    output_folder=root,
                    reactivated_csv_path=reactivated_csv,
                    create_native_pivot=True,
                    overwrite=True,
                    progress_callback=stages.append,
                )

        self.assertEqual(
            stages,
            [
                "Reading Hosted Players",
                "Comparing UIDs",
                "Reading Reactivated Players",
                "Building workbook",
                "Validating",
                "Creating PivotTables",
                "Validating",
                "Publishing",
            ],
        )

    def test_run_uid_handoff_emits_ordered_stage_names(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            stages: list[str] = []
            hosted_csv = write_hosted_csv(root / "hosted.csv", [hosted_row()])
            prior = write_prior_workbook(root / "prior.xlsx", "Baton Rouge", ["999"])

            run_uid_handoff(
                hosted_csv_path=hosted_csv,
                last_week_xlsx_path=prior,
                market="Baton Rouge",
                report_date=date(2026, 6, 1),
                output_folder=root,
                progress_callback=stages.append,
            )

        self.assertEqual(stages, ["Reading Hosted Players", "Comparing UIDs"])


if __name__ == "__main__":
    unittest.main()
