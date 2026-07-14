from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from hpr.errors import InputValidationError
from hpr.read_tableau import read_hosted_players_csv
from hpr.schema import HOSTED_COLUMNS
from tests.fixtures.report_data import hosted_row, write_tableau_tsv


class CsvIoTests(unittest.TestCase):
    def test_invalid_date_error_identifies_file_row_column_value_and_expected_format(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "hosted.csv"
            row = hosted_row(**{"Last Rated Day": "not-a-date"})
            write_tableau_tsv(path, HOSTED_COLUMNS, [row])

            with self.assertRaises(InputValidationError) as caught:
                read_hosted_players_csv(path)

            message = str(caught.exception)
            self.assertIn("hosted.csv", message)
            self.assertIn("row 2", message)
            self.assertIn("Last Rated Day", message)
            self.assertIn("not-a-date", message)
            self.assertIn("M/D/YYYY", message)

    def test_invalid_number_error_identifies_file_row_column_value_and_expected_format(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "hosted.csv"
            row = hosted_row(**{"Trips in Last 90 Days": "many"})
            write_tableau_tsv(path, HOSTED_COLUMNS, [row])

            with self.assertRaises(InputValidationError) as caught:
                read_hosted_players_csv(path)

            message = str(caught.exception)
            self.assertIn("hosted.csv", message)
            self.assertIn("row 2", message)
            self.assertIn("Trips in Last 90 Days", message)
            self.assertIn("many", message)
            self.assertIn("number", message)

    def test_missing_columns_identifies_file_and_required_columns(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "hosted.csv"
            columns = [column for column in HOSTED_COLUMNS if column != "Universal Player ID"]
            write_tableau_tsv(path, columns, [hosted_row()])

            with self.assertRaises(InputValidationError) as caught:
                read_hosted_players_csv(path)

            message = str(caught.exception)
            self.assertIn("hosted.csv", message)
            self.assertIn("Universal Player ID", message)
            self.assertIn("detected columns", message)


if __name__ == "__main__":
    unittest.main()
