class HostedPlayersReportError(Exception):
    """Base class for expected report workflow errors."""

    category = "INTERNAL"


class InputValidationError(HostedPlayersReportError):
    """The input is readable but invalid for this workflow."""

    category = "INVALID_INPUT"


class WorkbookAccessError(HostedPlayersReportError):
    """The input workbook cannot be opened or inspected."""

    category = "WORKBOOK_ACCESS"


class WorkbookBuildError(HostedPlayersReportError):
    """Workbook construction or validation failed."""

    category = "WORKBOOK_BUILD"


class ReconciliationError(WorkbookBuildError):
    """Source and workbook data failed reconciliation."""

    category = "RECONCILIATION"


class ExcelAutomationError(HostedPlayersReportError):
    """Required Excel automation did not complete."""

    category = "EXCEL_AUTOMATION"


class OutputPublicationError(HostedPlayersReportError):
    """Final workbook couldn't be published safely."""

    category = "OUTPUT_PUBLICATION"


class WorkbookLockedError(OutputPublicationError):
    """Excel or OneDrive has locked the output workbook."""

    def __init__(self, path: object) -> None:
        self.path = path
        super().__init__(
            "Could not save the workbook because it is locked: "
            f"{path}. Close this file in Excel, wait a few seconds for OneDrive to release it, "
            "then retry."
        )


class MarketInferenceError(InputValidationError):
    """Property IDs could not be mapped to a single market."""
