"""Report columns and workbook formats."""

from datetime import date

HOSTED_COLUMNS = [
    "Property ID",
    "Current Host Name",
    "Universal Player ID",
    "Guest ID",
    "Name Full",
    "Tier",
    "Trips in Last 90 Days",
    "Last Rated Day",
    "Days Since Last Visit",
    "Normal Days In Between Visits",
    "Visit Var",
    "Last 90 ADT",
    "Total Theo ",
]

REACTIVATED_COLUMNS = [
    "Property ID",
    "Current Host Name",
    "Universal Player ID",
    "Guest ID",
    "Name Full",
    "Tier",
    "Last Rated Day",
    "Slot Promo Cash In Amt",
    "Slot Theo",
    "Table Theo",
    "Sportsbook Theo",
    "Total Theo",
]

DATE_COLUMNS = {"Last Rated Day"}

TEXT_COLUMNS = {
    "Property ID",
    "Current Host Name",
    "Universal Player ID",
    "Name Full",
    "Tier",
}

HOSTED_SUM_COLUMNS = ["Total Theo "]

REACTIVATED_SUM_COLUMNS = [
    "Slot Promo Cash In Amt",
    "Slot Theo",
    "Table Theo",
    "Sportsbook Theo",
    "Total Theo",
]

EXCEL_CURRENCY_FORMAT = '"$"#,##0_);[Red]\\("$"#,##0\\);"-"'

HOSTED_COLUMN_WIDTHS = {
    "A": 10,
    "B": 21,
    "C": 17,
    "D": 10,
    "E": 30,
    "F": 12,
    "G": 19,
    "H": 14,
    "I": 18,
    "J": 27,
    "K": 8,
    "L": 12,
    "M": 12,
}

REACTIVATED_COLUMN_WIDTHS = {
    "A": 10,
    "B": 21,
    "C": 17,
    "D": 10,
    "E": 30,
    "F": 12,
    "G": 14,
    "H": 22,
    "I": 10,
    "J": 11,
    "K": 16,
    "L": 11,
}

SUMMARY_COLUMN_WIDTHS = {
    "A": 3,
    "B": 28,
    "C": 9,
    "D": 19,
}

REACTIVATION_SUMMARY_COLUMN_WIDTHS = {
    "A": 3,
    "B": 28,
    "C": 9,
    "D": 30,
    "E": 17,
    "F": 19,
    "G": 24,
    "H": 18,
}

SUMMARY_TITLE_FONT = "Trade Gothic Next Cond"


def summary_date_label(report_date: date) -> str:

    return f"As of {report_date:%A, %B} {report_date.day}, {report_date:%Y}"
