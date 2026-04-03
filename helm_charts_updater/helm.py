"""Helm chart operations for helm-charts-updater.

This module provides functionality to parse, update, and manage
Helm chart versions.
"""

import logging
import subprocess
from pathlib import Path

import semver
from pydantic import ValidationError
from ruamel.yaml import YAML
from ruamel.yaml import YAMLError
from ruamel.yaml.scalarstring import LiteralScalarString

from helm_charts_updater import config
from helm_charts_updater.exceptions import ChartValidationError
from helm_charts_updater.exceptions import NoUpdateNeededError
from helm_charts_updater.models import Chart


class HelmChart:
    """Manages Helm chart version updates.

    Handles parsing, modifying, and writing Chart.yaml files for Helm charts.

    Attributes:
        clone_path: Path to the cloned repository.
        charts_path: Relative path to charts directory within the repository.
        chart_name: Name of the chart to update.
        app_version: New application version to set.
    """

    def __init__(self) -> None:
        """Initialize HelmChart with configuration values."""
        self.clone_path = config.get_clone_path()
        self.charts_path = config.get_charts_path()
        self.chart_name = config.get_chart_name()
        self.app_version = config.get_app_version()

    def _get_chart_path(self) -> Path:
        """Get the path to the Chart.yaml file.

        Returns:
            Path to the Chart.yaml file for this chart.
        """
        return Path(self.clone_path) / self.charts_path / self.chart_name / "Chart.yaml"

    def parse_charts_yaml(self) -> Chart:
        """Parse the Chart.yaml file and return a Chart model.

        Returns:
            A Chart model instance populated from the Chart.yaml file.

        Raises:
            ChartValidationError: If the Chart.yaml file fails validation.
        """
        logging.info("Parsing %s's Chart.yaml...", self.chart_name)
        yaml = YAML(typ="rt")

        chart_path = self._get_chart_path()
        with open(chart_path, "r", encoding="utf-8") as f:
            chart_content = f.read()

        try:
            data = yaml.load(chart_content)
        except YAMLError as err:
            raise ChartValidationError(str(chart_path), str(err)) from err

        if not isinstance(data, dict):
            raise ChartValidationError(
                str(chart_path),
                f"Expected a YAML mapping, got {type(data).__name__}",
            )

        try:
            return Chart(**data)
        except (ValidationError, TypeError) as err:
            raise ChartValidationError(str(chart_path), str(err)) from err

    def update_chart_version(self) -> tuple[str, str | None]:
        """Update the chart version and appVersion in Chart.yaml.

        Bumps the patch version of the chart and updates the appVersion
        to the configured value. Optionally updates chart annotations
        for Artifact Hub changelog.

        Returns:
            A tuple of (new_chart_version, old_app_version). old_app_version
            may be None if the chart has no appVersion set.

        Raises:
            NoUpdateNeededError: If the appVersion is already up to date.
            ChartValidationError: If the Chart.yaml file fails validation.
        """
        chart = self.parse_charts_yaml()

        chart_version = str(semver.Version.parse(chart.version).bump_patch())
        app_version = self.app_version
        old_app_version = chart.appVersion

        if app_version == old_app_version:
            raise NoUpdateNeededError(
                f"No need to update {self.chart_name} chart version — "
                f"appVersion is already {app_version}"
            )

        if config.update_chart_annotations():
            if chart.annotations is None:
                chart.annotations = {}

            chart.annotations["artifacthub.io/changes"] = LiteralScalarString(
                f"- kind: changed\n  description: Update {self.chart_name} "
                f"app version from {old_app_version} to {app_version}\n"
            )

        logging.info("Bumping chart version from %s to %s", chart.version, chart_version)
        chart.version = chart_version  # Use already computed value

        logging.info("Bumping app version from %s to %s", chart.appVersion, app_version)
        chart.appVersion = app_version

        yaml = YAML(typ="rt")

        chart_path = self._get_chart_path()
        with open(chart_path, "w", encoding="utf-8") as f:
            yaml.dump(chart.model_dump(exclude_none=True), f)

        return chart_version, old_app_version

    def run_helm_docs(self) -> None:
        """Run helm-docs to generate chart documentation.

        Executes the helm-docs command to generate README documentation
        for the Helm chart.

        Raises:
            subprocess.CalledProcessError: If helm-docs command fails.
        """
        logging.info("Generating helm readme...")

        chart_dir = Path(self.clone_path) / self.charts_path / self.chart_name

        result = subprocess.run(
            ["helm-docs", "-c", str(chart_dir)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logging.error("helm-docs failed: %s", result.stderr.strip())
            raise subprocess.CalledProcessError(
                result.returncode, "helm-docs", output=result.stdout, stderr=result.stderr
            )
