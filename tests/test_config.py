"""Tests for the Config class."""

import os
from unittest.mock import patch

import pytest

from helm_charts_updater.config import CHART_NAME_PATTERN
from helm_charts_updater.config import Config


class TestChartNamePattern:
    """Tests for the chart name validation pattern."""

    @pytest.mark.parametrize(
        "name",
        [
            "my-chart",
            "myChart",
            "my_chart",
            "chart1",
            "a",
            "Chart-Name_123",
        ],
    )
    def test_valid_chart_names(self, name: str) -> None:
        """Test that valid chart names match the pattern."""
        assert CHART_NAME_PATTERN.match(name) is not None

    @pytest.mark.parametrize(
        "name",
        [
            "-invalid",
            "_invalid",
            "chart;rm -rf /",
            "chart&&echo",
            "chart|cat",
            "../escape",
            "",
            "chart name",
            "chart.name",
        ],
    )
    def test_invalid_chart_names(self, name: str) -> None:
        """Test that invalid chart names do not match the pattern."""
        assert CHART_NAME_PATTERN.match(name) is None


class TestConfig:
    """Tests for Config class."""

    def test_get_github_token(self, mock_env_vars: dict) -> None:
        """Test that get_github_token returns correct value."""
        config = Config()
        assert config.get_github_token() == "test-token-12345"

    def test_get_github_user(self, mock_env_vars: dict) -> None:
        """Test that get_github_user returns correct value."""
        config = Config()
        assert config.get_github_user() == "test-user"

    def test_get_github_repo(self, mock_env_vars: dict) -> None:
        """Test that get_github_repo returns correct value."""
        config = Config()
        assert config.get_github_repo() == "test-repo"

    def test_get_clone_path(self, mock_env_vars: dict) -> None:
        """Test that get_clone_path returns correct value."""
        config = Config()
        assert config.get_clone_path() == "/tmp/test-clone"

    def test_get_commit_author(self, mock_env_vars: dict) -> None:
        """Test that get_commit_author returns correct value."""
        config = Config()
        assert config.get_commit_author() == "Test Author"

    def test_get_commit_email(self, mock_env_vars: dict) -> None:
        """Test that get_commit_email returns correct value."""
        config = Config()
        assert config.get_commit_email() == "test@example.com"

    def test_get_chart_name_valid(self, mock_env_vars: dict) -> None:
        """Test that valid chart names are accepted."""
        config = Config()
        assert config.get_chart_name() == "test-chart"

    def test_get_chart_name_invalid_characters(self) -> None:
        """Test that invalid chart names are rejected."""
        with patch.dict(os.environ, {"INPUT_CHART_NAME": "chart;rm -rf /"}):
            config = Config()
            with pytest.raises(ValueError, match="Invalid chart name"):
                config.get_chart_name()

    def test_get_chart_name_starting_with_dash(self) -> None:
        """Test that chart names starting with dash are rejected."""
        with patch.dict(os.environ, {"INPUT_CHART_NAME": "-invalid"}):
            config = Config()
            with pytest.raises(ValueError, match="Invalid chart name"):
                config.get_chart_name()

    def test_get_charts_path(self, mock_env_vars: dict) -> None:
        """Test that get_charts_path returns correct value."""
        config = Config()
        assert config.get_charts_path() == "charts"

    def test_get_app_version(self, mock_env_vars: dict) -> None:
        """Test that get_app_version returns correct value."""
        config = Config()
        assert config.get_app_version() == "1.2.3"

    def test_generate_docs_true(self) -> None:
        """Test generate_docs returns True when set."""
        with patch.dict(os.environ, {"INPUT_GENERATE_DOCS": "true"}):
            config = Config()
            assert config.generate_docs() is True

    def test_generate_docs_false(self) -> None:
        """Test generate_docs returns False when set."""
        with patch.dict(os.environ, {"INPUT_GENERATE_DOCS": "false"}):
            config = Config()
            assert config.generate_docs() is False

    def test_update_readme_true(self) -> None:
        """Test update_readme returns True when set."""
        with patch.dict(os.environ, {"INPUT_UPDATE_README": "true"}):
            config = Config()
            assert config.update_readme() is True

    def test_update_readme_false(self) -> None:
        """Test update_readme returns False when set."""
        with patch.dict(os.environ, {"INPUT_UPDATE_README": "false"}):
            config = Config()
            assert config.update_readme() is False

    def test_update_chart_annotations_true(self) -> None:
        """Test update_chart_annotations returns True when set."""
        with patch.dict(os.environ, {"INPUT_UPDATE_CHART_ANNOTATIONS": "true"}):
            config = Config()
            assert config.update_chart_annotations() is True

    def test_update_chart_annotations_false(self) -> None:
        """Test update_chart_annotations returns False when set."""
        with patch.dict(os.environ, {"INPUT_UPDATE_CHART_ANNOTATIONS": "false"}):
            config = Config()
            assert config.update_chart_annotations() is False
