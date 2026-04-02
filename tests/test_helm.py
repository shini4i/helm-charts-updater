"""Tests for the HelmChart class."""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest

from helm_charts_updater.exceptions import ChartValidationError
from helm_charts_updater.exceptions import NoUpdateNeededError
from helm_charts_updater.helm import HelmChart
from helm_charts_updater.models import Chart


class TestHelmChartInit:
    """Tests for HelmChart initialization."""

    @patch("helm_charts_updater.helm.config")
    def test_init_sets_attributes(self, mock_config: MagicMock) -> None:
        """Test that __init__ sets all attributes from config."""
        mock_config.get_clone_path.return_value = "/mock/clone"
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "my-chart"
        mock_config.get_app_version.return_value = "2.0.0"

        helm = HelmChart()

        assert helm.clone_path == "/mock/clone"
        assert helm.charts_path == "charts"
        assert helm.chart_name == "my-chart"
        assert helm.app_version == "2.0.0"


class TestHelmChartParseYaml:
    """Tests for HelmChart YAML parsing."""

    @patch("helm_charts_updater.helm.config")
    def test_parse_charts_yaml_success(
        self, mock_config: MagicMock, sample_chart_yaml: str
    ) -> None:
        """Test parsing a valid Chart.yaml file."""
        mock_config.get_clone_path.return_value = "/mock"
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "1.0.0"

        with patch("builtins.open", mock_open(read_data=sample_chart_yaml)):
            helm = HelmChart()
            chart = helm.parse_charts_yaml()

            assert isinstance(chart, Chart)
            assert chart.name == "test-chart"
            assert chart.version == "1.0.0"
            assert chart.appVersion == "1.0.0"

    @patch("helm_charts_updater.helm.config")
    def test_parse_charts_yaml_invalid_raises_validation_error(
        self, mock_config: MagicMock
    ) -> None:
        """Test that invalid Chart.yaml raises ChartValidationError."""
        mock_config.get_clone_path.return_value = "/mock"
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "1.0.0"

        invalid_yaml = """
name: test-chart
description: Test
version: invalid-version
"""

        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            helm = HelmChart()
            with pytest.raises(ChartValidationError) as exc_info:
                helm.parse_charts_yaml()

            assert "test-chart" in str(exc_info.value)
            assert "not a valid semantic version" in exc_info.value.detail


class TestHelmChartUpdateVersion:
    """Tests for HelmChart version update."""

    @patch("helm_charts_updater.helm.config")
    def test_update_chart_version_raises_when_unchanged(
        self, mock_config: MagicMock, sample_chart_yaml: str
    ) -> None:
        """Test that NoUpdateNeededError is raised when appVersion is unchanged."""
        mock_config.get_clone_path.return_value = "/mock"
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "1.0.0"  # Same as in chart
        mock_config.update_chart_annotations.return_value = False

        with patch("builtins.open", mock_open(read_data=sample_chart_yaml)):
            helm = HelmChart()
            with pytest.raises(NoUpdateNeededError) as exc_info:
                helm.update_chart_version()

            assert "test-chart" in str(exc_info.value)

    @patch("helm_charts_updater.helm.config")
    def test_update_chart_version_bumps_version(
        self, mock_config: MagicMock, sample_chart_yaml: str
    ) -> None:
        """Test that chart version is bumped correctly."""
        mock_config.get_clone_path.return_value = "/mock"
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "2.0.0"  # Different from chart
        mock_config.update_chart_annotations.return_value = False

        mock_file = mock_open(read_data=sample_chart_yaml)
        with patch("builtins.open", mock_file):
            helm = HelmChart()
            chart_version, old_version = helm.update_chart_version()

            assert chart_version == "1.0.1"  # Patch bumped from 1.0.0
            assert old_version == "1.0.0"

    @patch("helm_charts_updater.helm.config")
    def test_update_chart_version_with_annotations(
        self, mock_config: MagicMock, sample_chart_yaml: str
    ) -> None:
        """Test that annotations are updated when enabled."""
        mock_config.get_clone_path.return_value = "/mock"
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "2.0.0"
        mock_config.update_chart_annotations.return_value = True

        mock_file = mock_open(read_data=sample_chart_yaml)
        with patch("builtins.open", mock_file):
            helm = HelmChart()
            helm.update_chart_version()

            # Verify file was written
            mock_file().write.assert_called()


class TestHelmChartRunDocs:
    """Tests for HelmChart helm-docs execution."""

    @patch("helm_charts_updater.helm.check_call")
    @patch("helm_charts_updater.helm.config")
    def test_run_helm_docs(
        self, mock_config: MagicMock, mock_check_call: MagicMock
    ) -> None:
        """Test helm-docs is called with correct arguments."""
        mock_config.get_clone_path.return_value = "/mock"
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "1.0.0"

        helm = HelmChart()
        helm.run_helm_docs()

        mock_check_call.assert_called_once()
        call_args = mock_check_call.call_args[0][0]
        assert call_args[0] == "helm-docs"
        assert call_args[1] == "-c"
        assert "test-chart" in call_args[2]


class TestHelmChartGetChartPath:
    """Tests for HelmChart path generation."""

    @patch("helm_charts_updater.helm.config")
    def test_get_chart_path(self, mock_config: MagicMock) -> None:
        """Test chart path generation."""
        mock_config.get_clone_path.return_value = "/mock/clone"
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "my-chart"
        mock_config.get_app_version.return_value = "1.0.0"

        helm = HelmChart()
        path = helm._get_chart_path()

        assert path == Path("/mock/clone/charts/my-chart/Chart.yaml")
