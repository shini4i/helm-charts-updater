"""Tests for the GitRepository class."""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from git import GitCommandError
from git import PushInfo
from git.remote import PushInfoList

from helm_charts_updater.exceptions import ChartValidationError
from helm_charts_updater.git import GitRepository
from helm_charts_updater.git import _sanitize_url


def push_info(flags: int, summary: str = "") -> MagicMock:
    """Build a fake PushInfo entry as returned by GitPython's Remote.push().

    Args:
        flags: Bitmask of PushInfo flags describing the outcome for one ref.
        summary: Human-readable summary line git printed for that ref.

    Returns:
        A MagicMock exposing the PushInfo attributes the code under test reads.
    """
    info = MagicMock()
    info.flags = flags
    info.summary = summary
    info.remote_ref_string = "refs/heads/main"
    return info


PUSH_OK = [push_info(PushInfo.FAST_FORWARD, "  abc123..def456  main -> main")]


def push_rejected() -> PushInfoList:
    """Build the push result GitPython returns for a non-fast-forward rejection.

    git exits non-zero and prints an `error:` line, so the list carries both a
    populated `error` attribute and a ref flagged ERROR|REJECTED.

    Returns:
        A PushInfoList shaped like a real rejected push.
    """
    infos = PushInfoList()
    infos.append(push_info(PushInfo.ERROR | PushInfo.REJECTED, "[rejected] (fetch first)"))
    infos.error = GitCommandError("push", 1, "error: failed to push some refs to 'origin'")
    return infos


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
    def test_generate_repo_url(self, mock_config: MagicMock) -> None:
        """Test URL generation with token."""
        mock_config.get_github_token.return_value = "test-token"
        mock_config.get_github_user.return_value = "test-user"
        mock_config.get_github_repo.return_value = "test-repo"

        url = GitRepository._generate_repo_url()

        assert "test-token" in url
        assert "test-user" in url
        assert "test-repo" in url
        assert url == "https://test-token@github.com/test-user/test-repo.git"

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch.object(Path, "exists", return_value=False)
    def test_token_not_stored_as_attribute(
        self,
        mock_exists: MagicMock,  # noqa: ARG002
        mock_repo: MagicMock,  # noqa: ARG002
        mock_config: MagicMock,
    ) -> None:
        """Test that the token URL is not stored as an instance attribute."""
        mock_config.get_github_token.return_value = "secret-token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/mock/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"

        git_repo = GitRepository()

        # Token should not be stored in any instance attribute
        for attr_value in vars(git_repo).values():
            assert "secret-token" not in str(attr_value)


class TestGitRepositoryClone:
    """Tests for GitRepository clone functionality."""

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch.object(Path, "exists")
    def test_clone_success(
        self, mock_exists: MagicMock, mock_repo: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test successful repository clone."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/mock/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        GitRepository()

        mock_repo.clone_from.assert_called_once()

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch.object(Path, "exists")
    def test_clone_path_exists_raises_error(
        self,
        mock_exists: MagicMock,
        mock_repo: MagicMock,  # noqa: ARG002
        mock_config: MagicMock,
    ) -> None:
        """Test that existing clone path raises FileExistsError."""
        mock_config.get_clone_path.return_value = "/mock/existing"
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
    @patch.object(Path, "exists")
    def test_clone_failure_sanitizes_error(
        self, mock_exists: MagicMock, mock_repo: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test that clone failure sanitizes error message."""
        mock_config.get_github_token.return_value = "secret-token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/mock/clone"
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
    @patch.object(Path, "exists")
    def test_push_changes_success(
        self, mock_exists: MagicMock, mock_repo_class: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test successful push."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/mock/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_remote.push.return_value = PUSH_OK
        mock_repo.remote.return_value = mock_remote
        mock_repo_class.return_value = mock_repo

        git_repo = GitRepository()
        git_repo.push_changes("1.0.1", "app", "1.2.3", "1.2.2")

        mock_remote.push.assert_called_once()

    @patch("helm_charts_updater.git.time.sleep")
    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch.object(Path, "exists")
    def test_push_changes_retries_on_rejection(
        self,
        mock_exists: MagicMock,
        mock_repo_class: MagicMock,
        mock_config: MagicMock,
        mock_sleep: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test push retries with rebase when the remote rejects the update.

        GitPython reports a rejected push through PushInfo flags, not by
        raising, so the retry must be driven off those flags.
        """
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/mock/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_remote.push.side_effect = [push_rejected(), PUSH_OK]
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
    @patch.object(Path, "exists")
    def test_push_changes_with_none_old_version(
        self, mock_exists: MagicMock, mock_repo_class: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test push with None old_version displays N/A in commit message."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/mock/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_remote.push.return_value = PUSH_OK
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

    @patch("helm_charts_updater.git.time.sleep")
    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch.object(Path, "exists")
    def test_push_changes_raises_when_retries_exhausted(
        self,
        mock_exists: MagicMock,
        mock_repo_class: MagicMock,
        mock_config: MagicMock,
        mock_sleep: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test that a persistently rejected push raises after all retries."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/mock/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_remote.push.return_value = push_rejected()
        mock_repo.remote.return_value = mock_remote
        mock_repo.active_branch.name = "main"
        mock_repo_class.return_value = mock_repo

        git_repo = GitRepository()

        with pytest.raises(GitCommandError) as exc_info:
            git_repo.push_changes("1.0.1", "app", "1.2.3", "1.2.2")

        assert "rejected" in str(exc_info.value)
        assert mock_remote.push.call_count == 3

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch.object(Path, "exists")
    def test_push_changes_fails_fast_on_non_retryable_failure(
        self, mock_exists: MagicMock, mock_repo_class: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test that a failure a rebase cannot fix is raised without retrying."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/mock/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_remote.push.return_value = [
            push_info(PushInfo.ERROR | PushInfo.REMOTE_FAILURE, "[remote failure]")
        ]
        mock_repo.remote.return_value = mock_remote
        mock_repo_class.return_value = mock_repo

        git_repo = GitRepository()

        with pytest.raises(GitCommandError):
            git_repo.push_changes("1.0.1", "app", "1.2.3", "1.2.2")

        assert mock_remote.push.call_count == 1
        mock_repo.git.pull.assert_not_called()

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch.object(Path, "exists")
    def test_push_changes_does_not_retry_remote_rejection(
        self, mock_exists: MagicMock, mock_repo_class: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test that a remote-side rejection is not retried.

        Branch protection and pre-receive hooks decline the same commit no
        matter how often it is rebased.
        """
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/mock/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_remote.push.return_value = [
            push_info(
                PushInfo.ERROR | PushInfo.REMOTE_REJECTED,
                "[remote rejected] (protected branch hook declined)",
            )
        ]
        mock_repo.remote.return_value = mock_remote
        mock_repo_class.return_value = mock_repo

        git_repo = GitRepository()

        with pytest.raises(GitCommandError) as exc_info:
            git_repo.push_changes("1.0.1", "app", "1.2.3", "1.2.2")

        assert mock_remote.push.call_count == 1
        mock_repo.git.pull.assert_not_called()
        assert "protected branch hook declined" in str(exc_info.value)

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch.object(Path, "exists")
    def test_push_changes_raises_when_push_list_carries_error(
        self, mock_exists: MagicMock, mock_repo_class: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test that a failed git invocation is caught even when the refs look clean.

        GitPython records the failure on the returned list's `error` attribute
        rather than raising; `raise_if_error()` consults only that attribute.
        """
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/mock/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        push_infos = PushInfoList()
        push_infos.append(push_info(PushInfo.FAST_FORWARD, "  abc..def  main -> main"))
        push_infos.error = GitCommandError("push", 1, "error: failed to push some refs")

        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_remote.push.return_value = push_infos
        mock_repo.remote.return_value = mock_remote
        mock_repo_class.return_value = mock_repo

        git_repo = GitRepository()

        with pytest.raises(GitCommandError) as exc_info:
            git_repo.push_changes("1.0.1", "app", "1.2.3", "1.2.2")

        assert "failed to push some refs" in str(exc_info.value)

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch.object(Path, "exists")
    def test_push_changes_raises_when_push_reports_nothing(
        self, mock_exists: MagicMock, mock_repo_class: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test that an empty push result is treated as a failure.

        GitPython returns an empty PushInfoList when the push fails entirely.
        """
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/mock/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_remote.push.return_value = []
        mock_repo.remote.return_value = mock_remote
        mock_repo_class.return_value = mock_repo

        git_repo = GitRepository()

        with pytest.raises(GitCommandError):
            git_repo.push_changes("1.0.1", "app", "1.2.3", "1.2.2")

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch.object(Path, "exists")
    def test_push_changes_sanitizes_git_command_error(
        self, mock_exists: MagicMock, mock_repo_class: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test that a token in a raised git error is masked before re-raising."""
        mock_config.get_github_token.return_value = "secret-token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/mock/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_remote.push.side_effect = GitCommandError(
            "push", 1, "fatal: https://secret-token@github.com/user/repo.git not found"
        )
        mock_repo.remote.return_value = mock_remote
        mock_repo_class.return_value = mock_repo

        git_repo = GitRepository()

        with pytest.raises(GitCommandError) as exc_info:
            git_repo.push_changes("1.0.1", "app", "1.2.3", "1.2.2")

        assert "secret-token" not in str(exc_info.value)


class TestGitRepositoryPullWithRebase:
    """Tests for GitRepository pull_with_rebase functionality."""

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch.object(Path, "exists")
    def test_pull_with_rebase_success(
        self, mock_exists: MagicMock, mock_repo_class: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test successful pull with rebase."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/mock/clone"
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
    @patch.object(Path, "exists")
    def test_pull_with_rebase_failure_reraises(
        self, mock_exists: MagicMock, mock_repo_class: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test that pull_with_rebase re-raises GitCommandError."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/mock/clone"
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


class TestGitRepositoryPushNonRejectionError:
    """Tests for push errors that are not rejections."""

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch.object(Path, "exists")
    def test_push_changes_reraises_non_rejection_error(
        self, mock_exists: MagicMock, mock_repo_class: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test that non-rejection push errors are re-raised without retry."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = "/mock/clone"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_remote = MagicMock()
        # Push fails with authentication error (not rejection)
        mock_remote.push.side_effect = GitCommandError(
            "push", 1, "Authentication failed for repository"
        )
        mock_repo.remote.return_value = mock_remote
        mock_repo_class.return_value = mock_repo

        git_repo = GitRepository()

        with pytest.raises(GitCommandError) as exc_info:
            git_repo.push_changes("1.0.1", "app", "1.2.3", "1.2.2")

        # Should have only tried push once (no retry)
        assert mock_remote.push.call_count == 1
        # Pull with rebase should NOT have been called
        mock_repo.git.pull.assert_not_called()
        # Error should be raised
        assert "Authentication failed" in str(exc_info.value)


class TestGitRepositoryGetChartsList:
    """Tests for get_charts_list functionality."""

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch.object(Path, "exists")
    def test_get_charts_list_finds_top_level_charts(
        self,
        mock_exists: MagicMock,
        mock_repo_class: MagicMock,
        mock_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that get_charts_list finds top-level Chart.yaml files."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = str(tmp_path)
        mock_config.get_charts_path.return_value = "."
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        # Create a top-level chart
        chart_dir = tmp_path / "my-chart"
        chart_dir.mkdir(parents=True)
        chart_yaml = chart_dir / "Chart.yaml"
        chart_yaml.write_text("""apiVersion: v2
name: my-chart
description: A test chart
version: 1.0.0
appVersion: "1.0.0"
""")

        git_repo = GitRepository()
        charts = git_repo.get_charts_list()

        assert len(charts) == 1
        assert charts[0].name == "my-chart"
        assert charts[0].version == "1.0.0"

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch.object(Path, "exists")
    def test_get_charts_list_filters_dependency_charts(
        self,
        mock_exists: MagicMock,
        mock_repo_class: MagicMock,
        mock_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that get_charts_list filters out dependency charts."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = str(tmp_path)
        mock_config.get_charts_path.return_value = "."
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        # Create a top-level chart
        chart_dir = tmp_path / "my-chart"
        chart_dir.mkdir(parents=True)
        chart_yaml = chart_dir / "Chart.yaml"
        chart_yaml.write_text("""apiVersion: v2
name: my-chart
description: A test chart
version: 1.0.0
""")

        # Create a dependency chart inside charts/ subdirectory
        dep_chart_dir = chart_dir / "charts" / "dependency"
        dep_chart_dir.mkdir(parents=True)
        dep_chart_yaml = dep_chart_dir / "Chart.yaml"
        dep_chart_yaml.write_text("""apiVersion: v2
name: dependency
description: A dependency chart
version: 2.0.0
""")

        git_repo = GitRepository()
        charts = git_repo.get_charts_list()

        # Should only find the top-level chart, not the dependency
        assert len(charts) == 1
        assert charts[0].name == "my-chart"

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch.object(Path, "exists")
    def test_get_charts_list_includes_top_level_charts_directory(
        self,
        mock_exists: MagicMock,
        mock_repo_class: MagicMock,
        mock_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that charts in a top-level charts/ directory are included."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = str(tmp_path)
        mock_config.get_charts_path.return_value = "charts"
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        # Create a chart in top-level charts/ directory (common repo structure)
        charts_dir = tmp_path / "charts" / "my-app"
        charts_dir.mkdir(parents=True)
        chart_yaml = charts_dir / "Chart.yaml"
        chart_yaml.write_text("""apiVersion: v2
name: my-app
description: An app chart
version: 1.0.0
""")

        # Create a dependency inside that chart (should be excluded)
        dep_dir = charts_dir / "charts" / "redis"
        dep_dir.mkdir(parents=True)
        dep_yaml = dep_dir / "Chart.yaml"
        dep_yaml.write_text("""apiVersion: v2
name: redis
description: Redis dependency
version: 6.0.0
""")

        git_repo = GitRepository()
        charts = git_repo.get_charts_list()

        # Should find the top-level charts/my-app but not charts/my-app/charts/redis
        assert len(charts) == 1
        assert charts[0].name == "my-app"

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch.object(Path, "exists")
    def test_get_charts_list_empty_directory(
        self,
        mock_exists: MagicMock,
        mock_repo_class: MagicMock,
        mock_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test get_charts_list returns empty list when no charts found."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = str(tmp_path)
        mock_config.get_charts_path.return_value = "."
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        git_repo = GitRepository()
        charts = git_repo.get_charts_list()

        assert len(charts) == 0

    @patch("helm_charts_updater.git.config")
    @patch("helm_charts_updater.git.Repo")
    @patch.object(Path, "exists")
    def test_get_charts_list_invalid_chart_raises_validation_error(
        self,
        mock_exists: MagicMock,
        mock_repo_class: MagicMock,
        mock_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that invalid Chart.yaml raises ChartValidationError."""
        mock_config.get_github_token.return_value = "token"
        mock_config.get_github_user.return_value = "user"
        mock_config.get_github_repo.return_value = "repo"
        mock_config.get_clone_path.return_value = str(tmp_path)
        mock_config.get_charts_path.return_value = "."
        mock_config.get_commit_author.return_value = "Author"
        mock_config.get_commit_email.return_value = "author@test.com"
        mock_exists.return_value = False

        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        # Create an invalid chart (missing required fields)
        chart_dir = tmp_path / "invalid-chart"
        chart_dir.mkdir(parents=True)
        chart_yaml = chart_dir / "Chart.yaml"
        chart_yaml.write_text("""apiVersion: v2
name: invalid-chart
# Missing required 'description' and 'version' fields
""")

        git_repo = GitRepository()

        with pytest.raises(ChartValidationError) as exc_info:
            git_repo.get_charts_list()

        assert "invalid-chart" in str(exc_info.value)
