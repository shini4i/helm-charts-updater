import tempfile
from unittest.mock import MagicMock
from unittest.mock import patch

from helm_charts_updater.git import GitRepository


@patch("helm_charts_updater.git.config")
@patch("helm_charts_updater.git.Repo", return_value=MagicMock())
def test_generate_repo_url(mock_repo, mock_config):
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = temp_dir
        git_repo = GitRepository()
        assert git_repo._generate_repo_url() == "https://token@github.com/user/repo.git"


@patch("helm_charts_updater.git.config")
@patch("helm_charts_updater.git.Repo", return_value=MagicMock())
def test_push_changes(mock_repo, mock_config):
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_config.get_clone_path.return_value = temp_dir
        git_repo = GitRepository()
        git_repo.local_repo = MagicMock()
        git_repo.push_changes("1.0.0", "app", "1.0.0", "0.9.0")
        git_repo.local_repo.remote.assert_called_once_with(name="origin")
        git_repo.local_repo.remote.return_value.push.assert_called_once()
