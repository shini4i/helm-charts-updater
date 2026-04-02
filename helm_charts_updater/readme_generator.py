"""README generation for helm-charts-updater.

This module provides functionality to update the repository README
with a table of available Helm charts.
"""

import logging
from pathlib import Path

from prettytable import PrettyTable
from prettytable import TableStyle

from helm_charts_updater import config
from helm_charts_updater.models import Chart


class Readme:
    """Manages README updates with a charts table.

    Updates the repository README.md file with a markdown table
    listing all available Helm charts and their versions.

    Attributes:
        readme_path: Path to the README.md file.
        readme_content: Current content of the README file.
        table_start_marker: HTML comment marking table start.
        table_end_marker: HTML comment marking table end.
    """

    def __init__(self) -> None:
        """Initialize Readme with the path to README.md."""
        self.readme_path = Path(config.get_clone_path()) / "README.md"
        self.readme_content = self._read_readme()

        self.table_start_marker = "<!-- table_start -->"
        self.table_end_marker = "<!-- table_end -->"

    def _read_readme(self) -> str:
        """Read the README file content.

        Returns:
            The content of the README file as a string.

        Raises:
            FileNotFoundError: If the README file does not exist.
        """
        with open(self.readme_path, "r", encoding="utf-8") as readme_file:
            return readme_file.read()

    @staticmethod
    def _generate_table(charts: list[Chart]) -> PrettyTable:
        """Generate a markdown table from the list of charts.

        Args:
            charts: List of Chart model instances.

        Returns:
            A PrettyTable configured for markdown output.
        """
        headers = ["Name", "Type", "Description", "Version", "App Version"]
        rows = []

        for chart in charts:
            rows.append(
                [
                    chart.name,
                    chart.type,
                    chart.description,
                    chart.version,
                    chart.appVersion,
                ]
            )

        table = PrettyTable(headers)
        table.set_style(TableStyle.MARKDOWN)
        table.add_rows(rows)
        table.sortby = "Name"

        return table

    def _replace_table(self, table: PrettyTable) -> None:
        """Replace the table content between markers in the README.

        Args:
            table: The PrettyTable to insert into the README.

        Raises:
            ValueError: If start or end marker is not found in the README,
                or if end marker appears before start marker.
        """
        logging.info("Replacing table...")

        start_pos = self.readme_content.find(self.table_start_marker)
        if start_pos == -1:
            raise ValueError(
                f"Table start marker '{self.table_start_marker}' not found in README. "
                "Please add the marker to your README.md file."
            )

        # Search for end marker AFTER start marker to avoid false matches
        end_pos = self.readme_content.find(self.table_end_marker, start_pos)
        if end_pos == -1:
            raise ValueError(
                f"Table end marker '{self.table_end_marker}' not found in README. "
                "Please add the marker to your README.md file."
            )

        # Calculate the position after the start marker, detecting the newline type
        marker_end = start_pos + len(self.table_start_marker)
        content_after_marker = self.readme_content[marker_end:]

        # Detect newline sequence (CRLF or LF)
        if content_after_marker.startswith("\r\n"):
            newline = "\r\n"
        elif content_after_marker.startswith("\n"):
            newline = "\n"
        else:
            newline = "\n"

        table_start = marker_end + len(newline) if content_after_marker.startswith(
            newline
        ) else marker_end

        # Use detected newline to preserve line endings
        table_content = table.get_string().replace("\n", newline)

        self.readme_content = (
            f"{self.readme_content[:table_start]}"
            f"{table_content}{newline}"
            f"{self.readme_content[end_pos:]}"
        )

    def update_readme(self, charts: list[Chart]) -> None:
        """Update the README with a table of charts.

        Generates a markdown table from the provided charts and
        replaces the content between the table markers in the README.

        Args:
            charts: List of Chart model instances to include in the table.

        Raises:
            ValueError: If table markers are not found in the README.
        """
        table = self._generate_table(charts)

        self._replace_table(table)

        logging.info("Writing new readme...")
        with open(self.readme_path, "w", encoding="utf-8") as readme_file:
            readme_file.write(self.readme_content)
