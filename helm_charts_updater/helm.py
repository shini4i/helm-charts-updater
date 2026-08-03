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
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.scalarstring import DoubleQuotedScalarString
from ruamel.yaml.scalarstring import LiteralScalarString
from ruamel.yaml.util import load_yaml_guess_indent

from helm_charts_updater.config import config
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
        yaml: Round-trip YAML parser, configured on load to match the chart file.
        newline: Line ending of the chart file, so writes do not convert it.
    """

    def __init__(self) -> None:
        """Initialize HelmChart with configuration values."""
        self.clone_path = config.get_clone_path()
        self.charts_path = config.get_charts_path()
        self.chart_name = config.get_chart_name()
        self.app_version = config.get_app_version()

        # ruamel's defaults would strip quotes and re-wrap scalars at 80 columns,
        # rewriting lines this tool never touched. Indentation is matched to the
        # source file in parse_charts_yaml().
        self.yaml = YAML(typ="rt")
        self.yaml.preserve_quotes = True
        self.yaml.width = 4096
        self.newline = "\n"

    def _get_chart_path(self) -> Path:
        """Get the path to the Chart.yaml file.

        Returns:
            Path to the Chart.yaml file for this chart.
        """
        return Path(self.clone_path) / self.charts_path / self.chart_name / "Chart.yaml"

    def parse_charts_yaml(self) -> tuple[CommentedMap, Chart]:
        """Parse the Chart.yaml file into a round-trip document and a Chart model.

        Returns both views of the same file. The document keeps the comments,
        key order and fields the Chart model does not define, so updates must
        be written back through it; the model is the validated view used to
        read known fields.

        Also matches this instance's emitter to the file just read: its line
        endings, whether it opens with a `---` marker, and its indentation.
        ruamel only reports one indent width, so when a file contains block
        sequences its mapping indent is not recovered and falls back to two.

        Returns:
            A tuple of (round-trip document, validated Chart model).

        Raises:
            ChartValidationError: If the Chart.yaml file fails validation.
        """
        logging.info("Parsing %s's Chart.yaml...", self.chart_name)

        chart_path = self._get_chart_path()
        with open(chart_path, "r", encoding="utf-8", newline="") as f:
            chart_content = f.read()

        self.newline = "\r\n" if "\r\n" in chart_content else "\n"
        # Charts linted with yamllint's default rules require the marker
        self.yaml.explicit_start = chart_content.lstrip().startswith("---")

        try:
            document, sequence_indent, offset = load_yaml_guess_indent(
                chart_content, yaml=self.yaml
            )
        except YAMLError as err:
            raise ChartValidationError(str(chart_path), str(err)) from err

        if sequence_indent is not None:
            if offset is None:
                # No block sequences, so the guessed width is the mapping indent
                self.yaml.indent(mapping=sequence_indent, sequence=sequence_indent, offset=0)
            elif 0 <= offset < sequence_indent:
                # A dash offset must leave room within the sequence indent, or
                # ruamel falls back to its own defaults anyway
                self.yaml.indent(sequence=sequence_indent, offset=offset)

        if not isinstance(document, CommentedMap):
            raise ChartValidationError(
                str(chart_path),
                f"Expected a YAML mapping, got {type(document).__name__}",
            )

        try:
            return document, Chart(**document)
        except (ValidationError, TypeError) as err:
            raise ChartValidationError(str(chart_path), str(err)) from err

    def update_chart_version(self) -> tuple[str, str | None]:
        """Update the chart version and appVersion in Chart.yaml.

        Bumps the patch version of the chart and updates the appVersion
        to the configured value. Optionally updates chart annotations
        for Artifact Hub changelog. Comments, key order and fields the
        Chart model does not define are left untouched.

        Returns:
            A tuple of (new_chart_version, old_app_version). old_app_version
            may be None if the chart has no appVersion set.

        Raises:
            NoUpdateNeededError: If the appVersion is already up to date.
            ChartValidationError: If the Chart.yaml file fails validation.
        """
        document, chart = self.parse_charts_yaml()

        chart_version = str(semver.Version.parse(chart.version).bump_patch())
        app_version = self.app_version
        old_app_version = chart.appVersion

        if app_version == old_app_version:
            raise NoUpdateNeededError(
                f"No need to update {self.chart_name} chart version — "
                f"appVersion is already {app_version}"
            )

        if config.update_chart_annotations():
            # A bare `annotations:` key parses to None, which cannot be indexed
            annotations = document.get("annotations")
            if not isinstance(annotations, CommentedMap):
                annotations = CommentedMap()
                document["annotations"] = annotations

            annotations["artifacthub.io/changes"] = LiteralScalarString(
                f"- kind: changed\n  description: Update {self.chart_name} "
                f"app version from {old_app_version} to {app_version}\n"
            )

        logging.info("Bumping chart version from %s to %s", chart.version, chart_version)
        document["version"] = chart_version

        logging.info("Bumping app version from %s to %s", old_app_version, app_version)
        # Quoted so a value like 1.10 is never read back as the float 1.1
        document["appVersion"] = DoubleQuotedScalarString(app_version)

        chart_path = self._get_chart_path()
        with open(chart_path, "w", encoding="utf-8", newline=self.newline) as f:
            self.yaml.dump(document, f)

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
