"""Tests for the GitRepository class."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from git import GitCommandError

from helm_charts_updater.git import GitRepository
from helm_charts_updater.git import _sanitize_url


class TestSanitizeUrl:
    """Tests for URL sanitization helper."""

    def test_sanitize_url_with_token(self) -> None:
        """Test that tokens are masked in URLs."""
        url = "https://ghp_secrettoken123@github.com/user/repo.git"
        result = _sanitize_url(url)
        assert result == "https://***@github.com/user/repo.git"
        assert "ghp_secrettoken123" not in result

    def test_sanitize_url_without_token(self) -> None:
        """Test that URLs without tokens are unchanged."""
        url = "https://github.com/user/repo.git"
        result = _sanitize_url(url)
        assert result == "https://github.com/user/repo.git"

    def test_sanitize_url_with_complex_token(self) -> None:
        """Test sanitization with complex token containing special chars."""
        url = "https://abc123_XYZ-456@github.com/user/repo.git"
        result = _sanitize_url(url)
        assert result == "https://***@github.com/user/repo.git"

    def test_sanitize_url_in_error_message(self) -> None:
        """Test sanitization in a typical error message."""
        error = "fatal: could not read from https://token123@github.com/user/repo.git"
        result = _sanitize_url(error)
        assert "token123" not in result
        assert "***" in result


class TestGitRepositoryGenerateUrl:
    """Tests for GitRepository URL generation."""

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch("os.path.exists")
    def test_generate_repo_url(
        self, mock_exists: MagicMock, mock_repo: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test URL generation with token."""
        mock_config.get_github_token.return_value = "test-token"
        mock_config.get_github_user.return_value = "test-user"
        mock_config.get_github_repo.return_value = "test-repo"
        mock_config.get_clone_path.return_value = "/tmp/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        repo = GitRepository()

        assert "test-token" in repo.repo
        assert "test-user" in repo.repo
        assert "test-repo" in repo.repo
        assert repo.repo == "https://test-token@github.com/test-user/test-repo.git"


class TestGitRepositoryClone:
    """Tests for GitRepository clone functionality."""

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch("os.path.exists")
    def test_clone_success(
        self, mock_exists: MagicMock, mock_repo: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test successful repository clone."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/tmp/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        GitRepository()

        mock_repo.clone_from.assert_called_once()

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch("os.path.exists")
    def test_clone_path_exists_raises_error(
        self, mock_exists: MagicMock, mock_repo: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test that existing clone path raises FileExistsError."""
        mock_config.get_clone_path.return_value = "/tmp/existing"
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = True

        with pytest.raises(FileExistsError) as exc_info:
            GitRepository()

        assert "already exists" in str(exc_info.value)

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch("os.path.exists")
    def test_clone_failure_sanitizes_error(
        self, mock_exists: MagicMock, mock_repo: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test that clone failure sanitizes error message."""
        mock_config.get_github_token.return_value = "secret-token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/tmp/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo.clone_from.side_effect = GitCommandError(
            "clone", 1, "https://secret-token@github.com/user/repo.git"
        )

        with pytest.raises(GitCommandError) as exc_info:
            GitRepository()

        # Token should be sanitized in the raised exception
        assert "secret-token" not in str(exc_info.value)


class TestGitRepositoryPush:
    """Tests for GitRepository push functionality."""

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch("os.path.exists")
    def test_push_changes_success(
        self, mock_exists: MagicMock, mock_repo_class: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test successful push."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/tmp/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_repo.remote.return_value = mock_remote
        mock_repo_class.return_value = mock_repo

        git_repo = GitRepository()
        git_repo.push_changes("1.0.1", "app", "1.2.3", "1.2.2")

        mock_remote.push.assert_called_once()

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch("os.path.exists")
    def test_push_changes_retries_on_rejection(
        self, mock_exists: MagicMock, mock_repo_class: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test push retries with rebase when updates are rejected."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/tmp/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_remote.push.side_effect = [
            GitCommandError("push", 1, "Updates were rejected"),
            None,
        ]
        mock_repo.remote.return_value = mock_remote
        mock_repo.active_branch.name = "main"
        mock_repo_class.return_value = mock_repo

        git_repo = GitRepository()
        git_repo.push_changes("1.0.1", "app", "1.2.3", "1.2.2")

        # Push should have been called twice (initial + retry)
        assert mock_remote.push.call_count == 2
        # Pull with rebase should have been called
        mock_repo.git.pull.assert_called_once()

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch("os.path.exists")
    def test_push_changes_with_none_old_version(
        self, mock_exists: MagicMock, mock_repo_class: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test push with None old_version displays N/A in commit message."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/tmp/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_repo.remote.return_value = mock_remote
        mock_repo_class.return_value = mock_repo

        git_repo = GitRepository()
        git_repo.push_changes("1.0.1", "app", "1.2.3", None)

        # Verify commit was called with N/A for old version
        commit_call = mock_repo.index.commit.call_args
        commit_message = commit_call[0][0]
        assert "N/A" in commit_message
        assert "1.2.3" in commit_message
        mock_remote.push.assert_called_once()

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch("os.path.exists")
    def test_push_changes_retry_failure_sanitizes_error(
        self, mock_exists: MagicMock, mock_repo_class: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test that retry push failure sanitizes error message."""
        mock_config.get_github_token.return_value = "secret-token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/tmp/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_remote = MagicMock()
        # First push fails with rejection, second push also fails
        mock_remote.push.side_effect = [
            GitCommandError("push", 1, "Updates were rejected"),
            GitCommandError("push", 1, "https://secret-token@github.com/user/repo.git failed"),
        ]
        mock_repo.remote.return_value = mock_remote
        mock_repo.active_branch.name = "main"
        mock_repo_class.return_value = mock_repo

        git_repo = GitRepository()

        with pytest.raises(GitCommandError) as exc_info:
            git_repo.push_changes("1.0.1", "app", "1.2.3", "1.2.2")

        # Token should be sanitized in the raised exception
        assert "secret-token" not in str(exc_info.value)


class TestGitRepositoryPullWithRebase:
    """Tests for GitRepository pull_with_rebase functionality."""

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch("os.path.exists")
    def test_pull_with_rebase_success(
        self, mock_exists: MagicMock, mock_repo_class: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test successful pull with rebase."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/tmp/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo_class.return_value = mock_repo

        git_repo = GitRepository()
        git_repo.pull_with_rebase()

        mock_repo.git.pull.assert_called_once()

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch("os.path.exists")
    def test_pull_with_rebase_failure_reraises(
        self, mock_exists: MagicMock, mock_repo_class: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test that pull_with_rebase re-raises GitCommandError."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/tmp/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo.git.pull.side_effect = GitCommandError("pull", 1, "conflict")
        mock_repo_class.return_value = mock_repo

        git_repo = GitRepository()

        with pytest.raises(GitCommandError):
            git_repo.pull_with_rebase()
