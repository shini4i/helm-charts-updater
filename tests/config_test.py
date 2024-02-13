from unittest.mock import MagicMock

import pytest

from helm_charts_updater.config import Config


@pytest.fixture
def mock_config():
    mock_env = MagicMock()
    config = Config()
    config.env = mock_env
    return config, mock_env


@pytest.mark.parametrize(
    "method_name, return_value, expected",
    [
        ("get_github_token", "test_token", "test_token"),
        ("get_github_user", "test_user", "test_user"),
        ("get_github_repo", "test_repo", "test_repo"),
        ("get_clone_path", "test_path", "test_path"),
        ("get_commit_author", "test_author", "test_author"),
        ("get_commit_email", "test_email", "test_email"),
        ("get_chart_name", "test_chart_name", "test_chart_name"),
        ("get_charts_path", "test_charts_path", "test_charts_path"),
        ("get_app_version", "test_app_version", "test_app_version"),
    ],
)
def test_config_methods(mock_config, method_name, return_value, expected):
    config, mock_env = mock_config
    mock_env.return_value = return_value
    assert getattr(config, method_name)() == expected
