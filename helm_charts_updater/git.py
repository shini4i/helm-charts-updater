"""Git repository operations for helm-charts-updater.

This module provides functionality to clone, commit, and push changes
to a GitHub repository containing Helm charts.
"""

import logging
import os
import re
import sys
from pathlib import Path

from git import GitCommandError
from git import Repo
from pydantic import ValidationError
from ruamel.yaml import YAML

from helm_charts_updater import config
from helm_charts_updater.models import Chart


def _sanitize_url(url: str) -> str:
    """Remove credentials from URL for safe logging.

    Args:
        url: A git URL that may contain embedded credentials.

    Returns:
        The URL with credentials replaced by '***'.
    """
    return re.sub(r"https://[^@]+@", "https://***@", url)


class GitRepository:
    """Manages Git operations for the Helm charts repository.

    Handles cloning, committing, and pushing changes to the charts repository.
    Includes automatic retry logic for push conflicts.

    Attributes:
        repo: The repository URL (with credentials).
        clone_path: Local path where the repository is cloned.
        commit_author: Git commit author name.
        committer_email: Git commit author email.
        yaml: YAML parser instance.
        local_repo: GitPython Repo instance for the cloned repository.
    """

    def __init__(self) -> None:
        """Initialize GitRepository by cloning the remote repository.

        Raises:
            FileExistsError: If the clone path already exists.
            GitCommandError: If cloning fails.
        """
        self.repo = self._generate_repo_url()
        self.clone_path = config.get_clone_path()

        self.commit_author = config.get_commit_author()
        self.committer_email = config.get_commit_email()

        self.yaml = YAML(typ="safe")

        self._clone()
        self.local_repo = Repo(self.clone_path)

    @staticmethod
    def _generate_repo_url() -> str:
        """Generate the GitHub repository URL with authentication token.

        Returns:
            The full repository URL with embedded token.
        """
        gh_token = config.get_github_token()
        gh_user = config.get_github_user()
        gh_repo = config.get_github_repo()

        return f"https://{gh_token}@github.com/{gh_user}/{gh_repo}.git"

    def _clone(self) -> None:
        """Clone the helm charts repository to the local path.

        Raises:
            FileExistsError: If the clone path already exists.
            GitCommandError: If cloning fails (with sanitized error message).
        """
        if not os.path.exists(self.clone_path):
            logging.info("Cloning helm charts repository to %s...", self.clone_path)
            try:
                Repo.clone_from(self.repo, self.clone_path)
            except GitCommandError as e:
                sanitized_error = _sanitize_url(str(e))
                logging.error("Failed to clone repository: %s", sanitized_error)
                raise GitCommandError(
                    command="clone",
                    status=1,
                    stderr=sanitized_error,
                ) from e
            return
        raise FileExistsError(
            f"Clone path '{self.clone_path}' already exists. "
            "Please remove it or use a different clone_path configuration."
        )

    def _commit_changes(self, commit_message: str) -> None:
        """Stage and commit all changes with the given message.

        Args:
            commit_message: The commit message to use.
        """
        self.local_repo.git.add(A=True)
        self.local_repo.git.config("user.name", self.commit_author)
        self.local_repo.git.config("user.email", self.committer_email)
        self.local_repo.index.commit(commit_message)

    def push_changes(
        self, chart_version: str, app_name: str, version: str, old_version: str | None
    ) -> None:
        """Commit and push chart version changes to the remote repository.

        If the push fails due to rejected updates, attempts to pull with rebase
        and retry the push.

        Args:
            chart_version: The new chart version.
            app_name: Name of the application/chart.
            version: The new application version.
            old_version: The previous application version, or None if not set.

        Raises:
            GitCommandError: If push fails for reasons other than rejected updates.
        """
        logging.info("Committing changes...")
        old_ver_display = old_version if old_version else "N/A"
        commit_message = (
            f"Bump {app_name} chart to {chart_version}\n"
            f"appVersion {old_ver_display} -> {version}"
        )

        self._commit_changes(commit_message)
        origin = self.local_repo.remote(name="origin")

        try:
            origin.push()
        except GitCommandError as error:
            sanitized_error = _sanitize_url(str(error))
            logging.error("Failed to push changes: %s", sanitized_error)
            if "Updates were rejected" in str(error):
                logging.info("Pulling changes with rebase and retrying push...")
                self.pull_with_rebase()
                try:
                    origin.push()
                except GitCommandError as retry_error:
                    sanitized_retry = _sanitize_url(str(retry_error))
                    logging.error("Retry push also failed: %s", sanitized_retry)
                    raise GitCommandError(
                        command="push",
                        status=1,
                        stderr=sanitized_retry,
                    ) from retry_error
            else:
                raise GitCommandError(
                    command="push",
                    status=1,
                    stderr=sanitized_error,
                ) from error

    def pull_with_rebase(self) -> None:
        """Pull latest changes from the remote repository with rebase.

        Uses 'ours' strategy to resolve conflicts in favor of local changes.

        Raises:
            GitCommandError: If the pull with rebase fails.
        """
        logging.info("Pulling latest changes from the remote repo with rebase...")
        origin = self.local_repo.remote(name="origin")
        try:
            self.local_repo.git.pull(
                origin,
                self.local_repo.active_branch.name,
                strategy_option="ours",
                rebase=True,
            )
        except GitCommandError as e:
            sanitized_error = _sanitize_url(str(e))
            logging.error("Error while pulling with rebase: %s", sanitized_error)
            raise GitCommandError(
                command="pull",
                status=1,
                stderr=sanitized_error,
            ) from e

    def get_charts_list(self) -> list[Chart]:
        """Get a list of all top-level Helm charts in the repository.

        Searches for Chart.yaml files and filters out dependency charts
        by checking if 'charts' appears in the relative path (indicating
        it's inside a dependency charts/ directory).

        Returns:
            A list of Chart model instances for each discovered chart.

        Raises:
            SystemExit: If a Chart.yaml file fails validation.
        """
        logging.info("Getting charts list...")

        charts: list[Chart] = []
        clone_path = Path(self.clone_path)

        for chart_path in clone_path.rglob("Chart.yaml"):
            # Filter out dependency charts by checking if 'charts' appears
            # in the relative path (dependency charts are in charts/ subdirs)
            try:
                rel_path = chart_path.relative_to(clone_path)
            except ValueError:
                continue

            # Skip if 'charts' appears in path parts (indicates dependency)
            if "charts" in rel_path.parts:
                continue

            with open(chart_path, encoding="utf-8") as file:
                try:
                    charts.append(Chart(**self.yaml.load(file)))
                except ValidationError as err:
                    logging.error("Failed to parse %s: %s", chart_path, err)
                    sys.exit(1)

        return charts
