"""Tests for the main module."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from helm_charts_updater.exceptions import ChartValidationError
from helm_charts_updater.exceptions import NoUpdateNeededError
from helm_charts_updater.main import main


class TestMain:
    """Tests for the main function."""

    @patch("helm_charts_updater.main.Readme")
    @patch("helm_charts_updater.main.HelmChart")
    @patch("helm_charts_updater.main.GitRepository")
    @patch("helm_charts_updater.main.config")
    def test_main_basic_workflow(
        self,
        mock_config: MagicMock,
        mock_git_repo_class: MagicMock,
        mock_helm_chart_class: MagicMock,
        mock_readme_class: MagicMock,
    ) -> None:
        """Test basic workflow without optional features."""
        mock_config.generate_docs.return_value = False
        mock_config.update_readme.return_value = False

        mock_repo = MagicMock()
        mock_git_repo_class.return_value = mock_repo

        mock_chart = MagicMock()
        mock_chart.update_chart_version.return_value = ("1.0.1", "1.0.0")
        mock_chart.chart_name = "test-chart"
        mock_chart.app_version = "2.0.0"
        mock_helm_chart_class.return_value = mock_chart

        main()

        # Verify GitRepository was created
        mock_git_repo_class.assert_called_once()

        # Verify HelmChart was created and version updated
        mock_helm_chart_class.assert_called_once()
        mock_chart.update_chart_version.assert_called_once()

        # Verify docs and readme were not generated
        mock_chart.run_helm_docs.assert_not_called()
        mock_readme_class.assert_not_called()

        # Verify push was called
        mock_repo.push_changes.assert_called_once_with(
            chart_version="1.0.1",
            app_name="test-chart",
            version="2.0.0",
            old_version="1.0.0",
        )

    @patch("helm_charts_updater.main.Readme")
    @patch("helm_charts_updater.main.HelmChart")
    @patch("helm_charts_updater.main.GitRepository")
    @patch("helm_charts_updater.main.config")
    def test_main_with_docs_generation(
        self,
        mock_config: MagicMock,
        mock_git_repo_class: MagicMock,
        mock_helm_chart_class: MagicMock,
        mock_readme_class: MagicMock,
    ) -> None:
        """Test workflow with helm-docs generation enabled."""
        mock_config.generate_docs.return_value = True
        mock_config.update_readme.return_value = False

        mock_repo = MagicMock()
        mock_git_repo_class.return_value = mock_repo

        mock_chart = MagicMock()
        mock_chart.update_chart_version.return_value = ("1.0.1", "1.0.0")
        mock_chart.chart_name = "test-chart"
        mock_chart.app_version = "2.0.0"
        mock_helm_chart_class.return_value = mock_chart

        main()

        # Verify helm-docs was run
        mock_chart.run_helm_docs.assert_called_once()

        # Verify README was not updated
        mock_readme_class.assert_not_called()

    @patch("helm_charts_updater.main.Readme")
    @patch("helm_charts_updater.main.HelmChart")
    @patch("helm_charts_updater.main.GitRepository")
    @patch("helm_charts_updater.main.config")
    def test_main_with_readme_update(
        self,
        mock_config: MagicMock,
        mock_git_repo_class: MagicMock,
        mock_helm_chart_class: MagicMock,
        mock_readme_class: MagicMock,
    ) -> None:
        """Test workflow with README update enabled."""
        mock_config.generate_docs.return_value = False
        mock_config.update_readme.return_value = True

        mock_repo = MagicMock()
        mock_repo.get_charts_list.return_value = [MagicMock()]
        mock_git_repo_class.return_value = mock_repo

        mock_chart = MagicMock()
        mock_chart.update_chart_version.return_value = ("1.0.1", "1.0.0")
        mock_chart.chart_name = "test-chart"
        mock_chart.app_version = "2.0.0"
        mock_helm_chart_class.return_value = mock_chart

        mock_readme = MagicMock()
        mock_readme_class.return_value = mock_readme

        main()

        # Verify Readme was created and updated
        mock_readme_class.assert_called_once()
        mock_readme.update_readme.assert_called_once()

        # Verify charts list was fetched
        mock_repo.get_charts_list.assert_called_once()

    @patch("helm_charts_updater.main.Readme")
    @patch("helm_charts_updater.main.HelmChart")
    @patch("helm_charts_updater.main.GitRepository")
    @patch("helm_charts_updater.main.config")
    def test_main_full_workflow(
        self,
        mock_config: MagicMock,
        mock_git_repo_class: MagicMock,
        mock_helm_chart_class: MagicMock,
        mock_readme_class: MagicMock,
    ) -> None:
        """Test full workflow with all features enabled."""
        mock_config.generate_docs.return_value = True
        mock_config.update_readme.return_value = True

        mock_repo = MagicMock()
        mock_repo.get_charts_list.return_value = [MagicMock()]
        mock_git_repo_class.return_value = mock_repo

        mock_chart = MagicMock()
        mock_chart.update_chart_version.return_value = ("1.0.1", "1.0.0")
        mock_chart.chart_name = "test-chart"
        mock_chart.app_version = "2.0.0"
        mock_helm_chart_class.return_value = mock_chart

        mock_readme = MagicMock()
        mock_readme_class.return_value = mock_readme

        main()

        # Verify all features were executed
        mock_chart.run_helm_docs.assert_called_once()
        mock_readme_class.assert_called_once()
        mock_readme.update_readme.assert_called_once()
        mock_repo.push_changes.assert_called_once()

    @patch("helm_charts_updater.main.HelmChart")
    @patch("helm_charts_updater.main.GitRepository")
    @patch("helm_charts_updater.main.config")
    def test_main_no_update_needed_returns_cleanly(
        self,
        mock_config: MagicMock,  # noqa: ARG002
        mock_git_repo_class: MagicMock,
        mock_helm_chart_class: MagicMock,
    ) -> None:
        """Test that NoUpdateNeededError causes a clean return without push."""
        mock_repo = MagicMock()
        mock_git_repo_class.return_value = mock_repo

        mock_chart = MagicMock()
        mock_chart.update_chart_version.side_effect = NoUpdateNeededError("already up to date")
        mock_helm_chart_class.return_value = mock_chart

        main()

        # Should NOT push changes
        mock_repo.push_changes.assert_not_called()

    @patch("helm_charts_updater.main.HelmChart")
    @patch("helm_charts_updater.main.GitRepository")
    @patch("helm_charts_updater.main.config")
    def test_main_chart_validation_error_propagates(
        self,
        mock_config: MagicMock,  # noqa: ARG002
        mock_git_repo_class: MagicMock,
        mock_helm_chart_class: MagicMock,
    ) -> None:
        """Test that ChartValidationError propagates from main()."""
        mock_repo = MagicMock()
        mock_git_repo_class.return_value = mock_repo

        mock_chart = MagicMock()
        mock_chart.update_chart_version.side_effect = ChartValidationError(
            "/path/Chart.yaml", "invalid version"
        )
        mock_helm_chart_class.return_value = mock_chart

        with pytest.raises(ChartValidationError):
            main()

        mock_repo.push_changes.assert_not_called()

    @patch("helm_charts_updater.main.Readme")
    @patch("helm_charts_updater.main.HelmChart")
    @patch("helm_charts_updater.main.GitRepository")
    @patch("helm_charts_updater.main.config")
    def test_main_chart_validation_error_during_readme_update(
        self,
        mock_config: MagicMock,
        mock_git_repo_class: MagicMock,
        mock_helm_chart_class: MagicMock,
        mock_readme_class: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test that ChartValidationError from get_charts_list propagates."""
        mock_config.generate_docs.return_value = False
        mock_config.update_readme.return_value = True

        mock_repo = MagicMock()
        mock_repo.get_charts_list.side_effect = ChartValidationError(
            "/path/Chart.yaml", "missing required field"
        )
        mock_git_repo_class.return_value = mock_repo

        mock_chart = MagicMock()
        mock_chart.update_chart_version.return_value = ("1.0.1", "1.0.0")
        mock_chart.chart_name = "test-chart"
        mock_chart.app_version = "2.0.0"
        mock_helm_chart_class.return_value = mock_chart

        with pytest.raises(ChartValidationError):
            main()

        mock_repo.push_changes.assert_not_called()
