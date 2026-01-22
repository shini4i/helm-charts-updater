"""Tests for the Readme class."""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest
from prettytable import PrettyTable

from helm_charts_updater.models import Chart
from helm_charts_updater.readme_generator import Readme


class TestReadmeInit:
    """Tests for Readme initialization."""

    @patch("helm_charts_updater.readme_generator.config")
    def test_init_reads_readme(
        self, mock_config: MagicMock, sample_readme_with_markers: str
    ) -> None:
        """Test that __init__ reads the README file."""
        mock_config.get_clone_path.return_value = "/tmp/repo"

        with patch("builtins.open", mock_open(read_data=sample_readme_with_markers)):
            readme = Readme()

            assert readme.readme_content == sample_readme_with_markers
            assert readme.table_start_marker == "<!-- table_start -->"
            assert readme.table_end_marker == "<!-- table_end -->"


class TestReadmeGenerateTable:
    """Tests for table generation."""

    def test_generate_table_creates_markdown_table(self) -> None:
        """Test that _generate_table creates a properly formatted table."""
        charts = [
            Chart(
                name="chart-a",
                description="Description A",
                version="1.0.0",
                type="application",
                appVersion="1.0.0",
            ),
            Chart(
                name="chart-b",
                description="Description B",
                version="2.0.0",
                type="library",
                appVersion="2.0.0",
            ),
        ]

        table = Readme._generate_table(charts)

        assert isinstance(table, PrettyTable)
        table_str = table.get_string()
        assert "chart-a" in table_str
        assert "chart-b" in table_str
        assert "Description A" in table_str

    def test_generate_table_sorts_by_name(self) -> None:
        """Test that table is sorted by chart name."""
        charts = [
            Chart(
                name="zebra-chart",
                description="Zebra",
                version="1.0.0",
            ),
            Chart(
                name="alpha-chart",
                description="Alpha",
                version="1.0.0",
            ),
        ]

        table = Readme._generate_table(charts)

        # Table should be sorted, so alpha comes before zebra
        table_str = table.get_string()
        alpha_pos = table_str.find("alpha-chart")
        zebra_pos = table_str.find("zebra-chart")
        assert alpha_pos < zebra_pos

    def test_generate_table_empty_list(self) -> None:
        """Test table generation with empty chart list."""
        table = Readme._generate_table([])

        assert isinstance(table, PrettyTable)
        # Table should have headers but no data rows
        table_str = table.get_string()
        assert "Name" in table_str


class TestReadmeReplaceTable:
    """Tests for table replacement."""

    @patch("helm_charts_updater.readme_generator.config")
    def test_replace_table_success(
        self, mock_config: MagicMock, sample_readme_with_markers: str
    ) -> None:
        """Test successful table replacement."""
        mock_config.get_clone_path.return_value = "/tmp/repo"

        with patch("builtins.open", mock_open(read_data=sample_readme_with_markers)):
            readme = Readme()

        table = PrettyTable(["Name", "Type", "Description", "Version", "App Version"])
        table.add_row(["new-chart", "app", "New chart", "1.0.0", "1.0.0"])

        readme._replace_table(table)

        assert "new-chart" in readme.readme_content
        assert "<!-- table_start -->" in readme.readme_content
        assert "<!-- table_end -->" in readme.readme_content

    @patch("helm_charts_updater.readme_generator.config")
    def test_replace_table_missing_start_marker(
        self, mock_config: MagicMock, sample_readme_without_markers: str
    ) -> None:
        """Test that missing start marker raises IndexError."""
        mock_config.get_clone_path.return_value = "/tmp/repo"

        with patch("builtins.open", mock_open(read_data=sample_readme_without_markers)):
            readme = Readme()

        table = PrettyTable(["Name"])

        with pytest.raises(IndexError) as exc_info:
            readme._replace_table(table)

        assert "table_start" in str(exc_info.value)

    @patch("helm_charts_updater.readme_generator.config")
    def test_replace_table_missing_end_marker(self, mock_config: MagicMock) -> None:
        """Test that missing end marker raises IndexError."""
        mock_config.get_clone_path.return_value = "/tmp/repo"

        readme_content = """# README
<!-- table_start -->
Some content
"""  # No end marker

        with patch("builtins.open", mock_open(read_data=readme_content)):
            readme = Readme()

        table = PrettyTable(["Name"])

        with pytest.raises(IndexError) as exc_info:
            readme._replace_table(table)

        assert "table_end" in str(exc_info.value)

    @patch("helm_charts_updater.readme_generator.config")
    def test_replace_table_markers_wrong_order(self, mock_config: MagicMock) -> None:
        """Test that markers in wrong order raises IndexError."""
        mock_config.get_clone_path.return_value = "/tmp/repo"

        readme_content = """# README
<!-- table_end -->
Some content
<!-- table_start -->
"""  # End marker before start marker

        with patch("builtins.open", mock_open(read_data=readme_content)):
            readme = Readme()

        table = PrettyTable(["Name"])

        with pytest.raises(IndexError) as exc_info:
            readme._replace_table(table)

        assert "start marker must appear before end marker" in str(exc_info.value)

    @patch("helm_charts_updater.readme_generator.config")
    def test_replace_table_with_crlf_line_endings(self, mock_config: MagicMock) -> None:
        """Test table replacement with CRLF line endings (Windows-style)."""
        mock_config.get_clone_path.return_value = "/tmp/repo"

        # README with CRLF line endings
        readme_content = (
            "# README\r\n"
            "<!-- table_start -->\r\n"
            "old content\r\n"
            "<!-- table_end -->\r\n"
            "## Footer\r\n"
        )

        with patch("builtins.open", mock_open(read_data=readme_content)):
            readme = Readme()

        table = PrettyTable(["Name", "Version"])
        table.add_row(["test-chart", "1.0.0"])

        readme._replace_table(table)

        # Verify markers are preserved
        assert "<!-- table_start -->" in readme.readme_content
        assert "<!-- table_end -->" in readme.readme_content
        # Verify new content is present
        assert "test-chart" in readme.readme_content
        # Verify surrounding content is preserved
        assert "# README" in readme.readme_content
        assert "## Footer" in readme.readme_content

    @patch("helm_charts_updater.readme_generator.config")
    def test_replace_table_no_newline_after_marker(self, mock_config: MagicMock) -> None:
        """Test table replacement when there's no newline after start marker."""
        mock_config.get_clone_path.return_value = "/tmp/repo"

        # README with no newline immediately after start marker
        readme_content = "<!-- table_start -->old content\n<!-- table_end -->"

        with patch("builtins.open", mock_open(read_data=readme_content)):
            readme = Readme()

        table = PrettyTable(["Name"])
        table.add_row(["test-chart"])

        readme._replace_table(table)

        # Verify markers and content
        assert "<!-- table_start -->" in readme.readme_content
        assert "<!-- table_end -->" in readme.readme_content
        assert "test-chart" in readme.readme_content


class TestReadmeUpdateReadme:
    """Tests for full README update."""

    @patch("helm_charts_updater.readme_generator.config")
    def test_update_readme_writes_file(
        self, mock_config: MagicMock, sample_readme_with_markers: str
    ) -> None:
        """Test that update_readme writes the updated content with correct data."""
        mock_config.get_clone_path.return_value = "/tmp/repo"

        charts = [
            Chart(
                name="updated-chart",
                description="Updated chart",
                version="3.0.0",
                type="application",
                appVersion="3.0.0",
            ),
        ]

        mock_file = mock_open(read_data=sample_readme_with_markers)
        with patch("builtins.open", mock_file):
            readme = Readme()
            readme.update_readme(charts)

            # Verify file was written with correct content
            mock_file().write.assert_called_once()
            written_content = mock_file().write.call_args[0][0]

            # Verify markers are preserved
            assert "<!-- table_start -->" in written_content
            assert "<!-- table_end -->" in written_content

            # Verify chart data is in the written content
            assert "updated-chart" in written_content
            assert "Updated chart" in written_content
            assert "3.0.0" in written_content
            assert "application" in written_content

            # Verify original surrounding content is preserved
            assert "# Charts Repository" in written_content
            assert "## Usage" in written_content

    @patch("helm_charts_updater.readme_generator.config")
    def test_update_readme_preserves_surrounding_content(
        self, mock_config: MagicMock, sample_readme_with_markers: str
    ) -> None:
        """Test that content before and after markers is preserved."""
        mock_config.get_clone_path.return_value = "/tmp/repo"

        charts = [
            Chart(
                name="test-chart",
                description="Test",
                version="1.0.0",
            ),
        ]

        with patch("builtins.open", mock_open(read_data=sample_readme_with_markers)):
            readme = Readme()
            readme.update_readme(charts)

            # Content before and after markers should be preserved
            assert "# Charts Repository" in readme.readme_content
            assert "## Usage" in readme.readme_content
