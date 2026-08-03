"""Tests for the HelmChart class."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest
from ruamel.yaml import YAML

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
            document, chart = helm.parse_charts_yaml()

            assert isinstance(chart, Chart)
            assert chart.name == "test-chart"
            assert chart.version == "1.0.0"
            assert chart.appVersion == "1.0.0"
            # The document keeps the file as written, for lossless round-tripping
            assert document["name"] == "test-chart"

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

    @patch("helm_charts_updater.helm.config")
    def test_parse_charts_yaml_malformed_yaml(self, mock_config: MagicMock) -> None:
        """Test that malformed YAML raises ChartValidationError."""
        mock_config.get_clone_path.return_value = "/mock"
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "1.0.0"

        malformed_yaml = "name: test\n  bad-indent: [unclosed"

        with patch("builtins.open", mock_open(read_data=malformed_yaml)):
            helm = HelmChart()
            with pytest.raises(ChartValidationError):
                helm.parse_charts_yaml()

    @patch("helm_charts_updater.helm.config")
    def test_parse_charts_yaml_empty_file(self, mock_config: MagicMock) -> None:
        """Test that empty file raises ChartValidationError."""
        mock_config.get_clone_path.return_value = "/mock"
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "1.0.0"

        with patch("builtins.open", mock_open(read_data="")):
            helm = HelmChart()
            with pytest.raises(ChartValidationError) as exc_info:
                helm.parse_charts_yaml()

            assert "NoneType" in exc_info.value.detail

    @patch("helm_charts_updater.helm.config")
    def test_parse_charts_yaml_non_mapping(self, mock_config: MagicMock) -> None:
        """Test that non-mapping YAML (e.g., a list) raises ChartValidationError."""
        mock_config.get_clone_path.return_value = "/mock"
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "1.0.0"

        list_yaml = "- item1\n- item2\n"

        with patch("builtins.open", mock_open(read_data=list_yaml)):
            helm = HelmChart()
            with pytest.raises(ChartValidationError) as exc_info:
                helm.parse_charts_yaml()

            assert "Expected a YAML mapping" in exc_info.value.detail


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


CHART_WITH_EXTRAS = """\
apiVersion: v2
name: test-chart
# Keep this comment — it explains the description below
description: A test Helm chart
home: https://example.com/test-chart
type: application
version: 1.0.0
appVersion: "1.0.0"
deprecated: false
"""


class TestHelmChartWritePreservesDocument:
    """Tests that updating a chart rewrites only the version fields."""

    @staticmethod
    def _write_chart(tmp_path: Path, content: str) -> Path:
        """Create a chart directory containing the given Chart.yaml content.

        Args:
            tmp_path: Pytest temporary directory used as the clone path.
            content: Chart.yaml content to write.

        Returns:
            Path to the written Chart.yaml.
        """
        chart_dir = tmp_path / "charts" / "test-chart"
        chart_dir.mkdir(parents=True)
        chart_yaml = chart_dir / "Chart.yaml"
        chart_yaml.write_text(content)
        return chart_yaml

    @patch("helm_charts_updater.helm.config")
    def test_update_preserves_comments_and_unmodelled_fields(
        self, mock_config: MagicMock, tmp_path: Path
    ) -> None:
        """Test that comments and fields outside the Chart model survive an update."""
        mock_config.get_clone_path.return_value = str(tmp_path)
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "2.0.0"
        mock_config.update_chart_annotations.return_value = False

        chart_yaml = self._write_chart(tmp_path, CHART_WITH_EXTRAS)

        HelmChart().update_chart_version()

        result = chart_yaml.read_text()
        assert "# Keep this comment" in result
        assert "home: https://example.com/test-chart" in result
        assert "deprecated: false" in result
        assert "version: 1.0.1" in result

    @patch("helm_charts_updater.helm.config")
    def test_update_preserves_key_order(self, mock_config: MagicMock, tmp_path: Path) -> None:
        """Test that an update does not reorder the keys of Chart.yaml."""
        mock_config.get_clone_path.return_value = str(tmp_path)
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "2.0.0"
        mock_config.update_chart_annotations.return_value = False

        chart_yaml = self._write_chart(tmp_path, CHART_WITH_EXTRAS)

        HelmChart().update_chart_version()

        keys = [line.split(":")[0] for line in chart_yaml.read_text().splitlines() if ":" in line]
        assert keys[:3] == ["apiVersion", "name", "description"]

    @patch("helm_charts_updater.helm.config")
    def test_update_keeps_app_version_a_string(
        self, mock_config: MagicMock, tmp_path: Path
    ) -> None:
        """Test that a numeric-looking appVersion is not written as a YAML number.

        An unquoted 1.10 would be read back as the float 1.1, silently
        corrupting the image tag the chart deploys.
        """
        mock_config.get_clone_path.return_value = str(tmp_path)
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "1.10"
        mock_config.update_chart_annotations.return_value = False

        chart_yaml = self._write_chart(tmp_path, CHART_WITH_EXTRAS)

        HelmChart().update_chart_version()

        yaml = YAML(typ="safe")
        with open(chart_yaml, encoding="utf-8") as f:
            data = yaml.load(f)

        assert data["appVersion"] == "1.10"

    @patch("helm_charts_updater.helm.config")
    def test_update_leaves_untouched_lines_byte_identical(
        self, mock_config: MagicMock, tmp_path: Path
    ) -> None:
        """Test that only the version lines change — quotes, wrapping and indentation hold."""
        mock_config.get_clone_path.return_value = str(tmp_path)
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "2.0.0"
        mock_config.update_chart_annotations.return_value = False

        original = (
            "apiVersion: v2\n"
            "name: test-chart\n"
            'description: "A quoted description long enough to run past the eighty column '
            'default that ruamel would otherwise wrap"\n'
            "version: 1.0.0\n"
            'appVersion: "1.0.0"\n'
            "maintainers:\n"
            "  - name: Test Maintainer\n"
            "    email: test@example.com\n"
        )
        chart_yaml = self._write_chart(tmp_path, original)

        HelmChart().update_chart_version()

        expected = original.replace("version: 1.0.0", "version: 1.0.1").replace(
            'appVersion: "1.0.0"', 'appVersion: "2.0.0"'
        )
        assert chart_yaml.read_text() == expected

    @patch("helm_charts_updater.helm.config")
    def test_update_preserves_document_start_marker(
        self, mock_config: MagicMock, tmp_path: Path
    ) -> None:
        """Test that a leading `---` survives.

        yamllint's default document-start rule requires it, so dropping the
        marker would make this tool push commits that fail the chart
        repository's own lint.
        """
        mock_config.get_clone_path.return_value = str(tmp_path)
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "2.0.0"
        mock_config.update_chart_annotations.return_value = False

        original = '---\napiVersion: v2\nname: test-chart\nversion: 1.0.0\nappVersion: "1.0.0"\n'
        chart_yaml = self._write_chart(tmp_path, original)

        HelmChart().update_chart_version()

        assert chart_yaml.read_text().startswith("---\n")

    @patch("helm_charts_updater.helm.config")
    def test_update_preserves_document_start_after_leading_comment(
        self, mock_config: MagicMock, tmp_path: Path
    ) -> None:
        """Test that a `---` marker is kept when comments precede it.

        YAML permits comments before the document start, so the marker is not
        necessarily the first characters in the file.
        """
        mock_config.get_clone_path.return_value = str(tmp_path)
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "2.0.0"
        mock_config.update_chart_annotations.return_value = False

        original = (
            "# Managed by automation\n"
            "---\n"
            "apiVersion: v2\n"
            "name: test-chart\n"
            "version: 1.0.0\n"
            'appVersion: "1.0.0"\n'
        )
        chart_yaml = self._write_chart(tmp_path, original)

        HelmChart().update_chart_version()

        assert "---\n" in chart_yaml.read_text()

    @patch("helm_charts_updater.helm.config")
    def test_update_adds_no_document_start_when_absent(
        self, mock_config: MagicMock, tmp_path: Path
    ) -> None:
        """Test that a chart without a `---` marker does not gain one."""
        mock_config.get_clone_path.return_value = str(tmp_path)
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "2.0.0"
        mock_config.update_chart_annotations.return_value = False

        original = (
            "# A comment, but no document start\n"
            "apiVersion: v2\n"
            "name: test-chart\n"
            "version: 1.0.0\n"
            'appVersion: "1.0.0"\n'
        )
        chart_yaml = self._write_chart(tmp_path, original)

        HelmChart().update_chart_version()

        assert not chart_yaml.read_text().startswith("---")

    @patch("helm_charts_updater.helm.config")
    def test_update_preserves_nested_mapping_indentation(
        self, mock_config: MagicMock, tmp_path: Path
    ) -> None:
        """Test that a four-space nested mapping is not re-indented to two."""
        mock_config.get_clone_path.return_value = str(tmp_path)
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "2.0.0"
        mock_config.update_chart_annotations.return_value = False

        original = (
            "apiVersion: v2\n"
            "name: test-chart\n"
            "version: 1.0.0\n"
            'appVersion: "1.0.0"\n'
            "annotations:\n"
            "    artifacthub.io/license: MIT\n"
        )
        chart_yaml = self._write_chart(tmp_path, original)

        HelmChart().update_chart_version()

        assert "    artifacthub.io/license: MIT" in chart_yaml.read_text()

    @patch("helm_charts_updater.helm.config")
    def test_update_preserves_crlf_line_endings(
        self, mock_config: MagicMock, tmp_path: Path
    ) -> None:
        """Test that a CRLF chart file is not rewritten to LF throughout."""
        mock_config.get_clone_path.return_value = str(tmp_path)
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "2.0.0"
        mock_config.update_chart_annotations.return_value = False

        chart_dir = tmp_path / "charts" / "test-chart"
        chart_dir.mkdir(parents=True)
        chart_yaml = chart_dir / "Chart.yaml"
        with open(chart_yaml, "w", encoding="utf-8", newline="") as f:
            f.write(
                'apiVersion: v2\r\nname: test-chart\r\nversion: 1.0.0\r\nappVersion: "1.0.0"\r\n'
            )

        HelmChart().update_chart_version()

        with open(chart_yaml, encoding="utf-8", newline="") as f:
            result = f.read()

        assert "\r\n" in result
        assert "version: 1.0.1\r\n" in result

    @patch("helm_charts_updater.helm.config")
    def test_update_keeps_other_annotations_on_a_repeat_run(
        self, mock_config: MagicMock, tmp_path: Path
    ) -> None:
        """Test the steady state: a chart already carrying annotations from a prior run."""
        mock_config.get_clone_path.return_value = str(tmp_path)
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "2.0.0"
        mock_config.update_chart_annotations.return_value = True

        original = (
            "apiVersion: v2\n"
            "name: test-chart\n"
            "version: 1.0.0\n"
            'appVersion: "1.0.0"\n'
            "annotations:\n"
            "  artifacthub.io/license: MIT\n"
            "  artifacthub.io/changes: |\n"
            "    - kind: changed\n"
            "      description: Update test-chart app version from 0.9.0 to 1.0.0\n"
        )
        chart_yaml = self._write_chart(tmp_path, original)

        HelmChart().update_chart_version()

        result = chart_yaml.read_text()
        yaml = YAML(typ="safe")
        with open(chart_yaml, encoding="utf-8") as f:
            data = yaml.load(f)

        # Unrelated annotations set by a maintainer must survive
        assert data["annotations"]["artifacthub.io/license"] == "MIT"
        changes = data["annotations"]["artifacthub.io/changes"]
        assert "from 1.0.0 to 2.0.0" in changes
        assert "0.9.0" not in changes
        assert "artifacthub.io/changes: |" in result
        assert result.count("annotations:") == 1

    @patch("helm_charts_updater.helm.config")
    def test_update_annotations_when_key_present_but_empty(
        self, mock_config: MagicMock, tmp_path: Path
    ) -> None:
        """Test that a valueless `annotations:` key is replaced rather than indexed."""
        mock_config.get_clone_path.return_value = str(tmp_path)
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "2.0.0"
        mock_config.update_chart_annotations.return_value = True

        chart_yaml = self._write_chart(tmp_path, CHART_WITH_EXTRAS + "annotations:\n")

        HelmChart().update_chart_version()

        yaml = YAML(typ="safe")
        with open(chart_yaml, encoding="utf-8") as f:
            data = yaml.load(f)

        assert "Update test-chart" in data["annotations"]["artifacthub.io/changes"]

    @patch("helm_charts_updater.helm.config")
    def test_update_adds_annotations_to_existing_document(
        self, mock_config: MagicMock, tmp_path: Path
    ) -> None:
        """Test that the changelog annotation is added without dropping other fields."""
        mock_config.get_clone_path.return_value = str(tmp_path)
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "2.0.0"
        mock_config.update_chart_annotations.return_value = True

        chart_yaml = self._write_chart(tmp_path, CHART_WITH_EXTRAS)

        HelmChart().update_chart_version()

        yaml = YAML(typ="safe")
        with open(chart_yaml, encoding="utf-8") as f:
            data = yaml.load(f)

        assert "Update test-chart app version from 1.0.0 to 2.0.0" in (
            data["annotations"]["artifacthub.io/changes"]
        )
        assert data["home"] == "https://example.com/test-chart"
        # Artifact Hub requires the changelog to be a YAML block scalar, which
        # the safe loader above would normalise away
        assert "artifacthub.io/changes: |" in chart_yaml.read_text()


class TestHelmChartRunDocs:
    """Tests for HelmChart helm-docs execution."""

    @patch("helm_charts_updater.helm.subprocess.run")
    @patch("helm_charts_updater.helm.config")
    def test_run_helm_docs_success(self, mock_config: MagicMock, mock_run: MagicMock) -> None:
        """Test helm-docs is called with correct arguments."""
        mock_config.get_clone_path.return_value = "/mock"
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "1.0.0"

        mock_run.return_value = subprocess.CompletedProcess(
            args=["helm-docs"], returncode=0, stdout="", stderr=""
        )

        helm = HelmChart()
        helm.run_helm_docs()

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "helm-docs"
        assert call_args[1] == "-c"
        assert "test-chart" in call_args[2]

    @patch("helm_charts_updater.helm.subprocess.run")
    @patch("helm_charts_updater.helm.config")
    def test_run_helm_docs_failure_logs_stderr(
        self, mock_config: MagicMock, mock_run: MagicMock
    ) -> None:
        """Test helm-docs failure raises CalledProcessError with stderr."""
        mock_config.get_clone_path.return_value = "/mock"
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_chart_name.return_value = "test-chart"
        mock_config.get_app_version.return_value = "1.0.0"

        mock_run.return_value = subprocess.CompletedProcess(
            args=["helm-docs"], returncode=1, stdout="", stderr="template error: bad syntax"
        )

        helm = HelmChart()
        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            helm.run_helm_docs()

        assert exc_info.value.returncode == 1
        assert "bad syntax" in exc_info.value.stderr


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
