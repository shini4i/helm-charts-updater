"""Shared pytest fixtures for helm-charts-updater tests."""

import os
from pathlib import Path
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_env_vars() -> Generator[dict[str, str], None, None]:
    """Fixture to set up required environment variables.

    Yields:
        Dictionary of environment variables that were set.
    """
    env_vars = {
        "INPUT_GITHUB_TOKEN": "test-token-12345",
        "INPUT_GH_USER": "test-user",
        "INPUT_GH_REPO": "test-repo",
        "INPUT_CLONE_PATH": "/mock/test-clone",
        "INPUT_COMMIT_AUTHOR": "Test Author",
        "INPUT_COMMIT_EMAIL": "test@example.com",
        "INPUT_CHART_NAME": "test-chart",
        "INPUT_CHARTS_PATH": "charts",
        "INPUT_APP_VERSION": "1.2.3",
        "INPUT_GENERATE_DOCS": "false",
        "INPUT_UPDATE_README": "false",
        "INPUT_UPDATE_CHART_ANNOTATIONS": "false",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def sample_chart_yaml() -> str:
    """Fixture providing valid Chart.yaml content.

    Returns:
        A string containing valid Chart.yaml YAML content.
    """
    return """apiVersion: v2
name: test-chart
description: A test Helm chart
type: application
version: 1.0.0
appVersion: "1.0.0"
maintainers:
  - name: Test Maintainer
    email: test@example.com
"""


@pytest.fixture
def sample_chart_data() -> dict[str, Any]:
    """Fixture providing valid Chart data as a dictionary.

    Returns:
        Dictionary with valid chart data.
    """
    return {
        "apiVersion": "v2",
        "name": "test-chart",
        "description": "A test Helm chart",
        "type": "application",
        "version": "1.0.0",
        "appVersion": "1.0.0",
    }


@pytest.fixture
def sample_readme_with_markers() -> str:
    """Fixture providing README content with table markers.

    Returns:
        A string containing README content with table markers.
    """
    return """# Charts Repository

This repository contains Helm charts.

<!-- table_start -->
| Name | Type | Description | Version | App Version |
|------|------|-------------|---------|-------------|
| old-chart | application | Old chart | 0.1.0 | 0.1.0 |
<!-- table_end -->

## Usage

Install charts using Helm.
"""


@pytest.fixture
def sample_readme_without_markers() -> str:
    """Fixture providing README content without table markers.

    Returns:
        A string containing README content without table markers.
    """
    return """# Charts Repository

This repository contains Helm charts.

## Usage

Install charts using Helm.
"""


@pytest.fixture
def mock_repo() -> MagicMock:
    """Fixture providing a mocked GitPython Repo object.

    Returns:
        A MagicMock configured to simulate a Repo object.
    """
    mock = MagicMock()
    mock.git = MagicMock()
    mock.index = MagicMock()
    mock.remote.return_value = MagicMock()
    mock.active_branch.name = "main"
    return mock


@pytest.fixture
def temp_chart_directory(tmp_path: Path, sample_chart_yaml: str) -> Path:
    """Fixture creating a temporary chart directory structure.

    Args:
        tmp_path: Pytest's temporary path fixture.
        sample_chart_yaml: Sample Chart.yaml content.

    Returns:
        Path to the temporary directory root.
    """
    charts_path = tmp_path / "charts" / "test-chart"
    charts_path.mkdir(parents=True)

    chart_yaml = charts_path / "Chart.yaml"
    chart_yaml.write_text(sample_chart_yaml)

    return tmp_path
