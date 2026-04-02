"""Custom exceptions for helm-charts-updater.

This module defines domain-specific exceptions used throughout the application
to handle expected error conditions without resorting to sys.exit().
"""


class NoUpdateNeededError(Exception):
    """Raised when the chart already has the desired appVersion.

    This is not an error condition — it signals that no work needs to be done.
    """


class ChartValidationError(Exception):
    """Raised when a Chart.yaml file fails Pydantic validation.

    Attributes:
        chart_path: The path to the invalid Chart.yaml file.
        detail: The validation error detail from Pydantic.
    """

    def __init__(self, chart_path: str, detail: str) -> None:
        """Initialize ChartValidationError.

        Args:
            chart_path: Path to the Chart.yaml that failed validation.
            detail: The Pydantic validation error message.
        """
        self.chart_path = chart_path
        self.detail = detail
        super().__init__(f"Failed to parse {chart_path}: {detail}")
