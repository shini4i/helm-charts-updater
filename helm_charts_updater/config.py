"""Configuration management for helm-charts-updater.

This module provides the Config class that handles reading and validating
configuration from environment variables.
"""

import re

from environs import Env

# Pattern for valid Helm chart names
# Must start with alphanumeric and contain only alphanumeric, dashes, and underscores
CHART_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\-_]*$")


class Config:
    """Configuration manager for the helm-charts-updater.

    Reads configuration from environment variables. All values are prefixed
    with INPUT_ to match GitHub Actions input conventions.

    Attributes:
        env: The environs Env instance for reading environment variables.
    """

    def __init__(self) -> None:
        """Initialize the Config with an environs Env instance."""
        self.env = Env()

    def get_github_token(self) -> str:
        """Get the GitHub authentication token.

        Returns:
            The GitHub token for repository access.

        Raises:
            environs.EnvError: If INPUT_GITHUB_TOKEN is not set.
        """
        return self.env.str("INPUT_GITHUB_TOKEN")

    def get_github_user(self) -> str:
        """Get the GitHub username or organization.

        Returns:
            The GitHub user/org that owns the charts repository.

        Raises:
            environs.EnvError: If INPUT_GH_USER is not set.
        """
        return self.env.str("INPUT_GH_USER")

    def get_github_repo(self) -> str:
        """Get the GitHub repository name.

        Returns:
            The name of the charts repository.

        Raises:
            environs.EnvError: If INPUT_GH_REPO is not set.
        """
        return self.env.str("INPUT_GH_REPO")

    def get_clone_path(self) -> str:
        """Get the local path for cloning the repository.

        Returns:
            The local filesystem path to clone into.

        Raises:
            environs.EnvError: If INPUT_CLONE_PATH is not set.
        """
        return self.env.str("INPUT_CLONE_PATH")

    def get_commit_author(self) -> str:
        """Get the Git commit author name.

        Returns:
            The author name to use for commits.

        Raises:
            environs.EnvError: If INPUT_COMMIT_AUTHOR is not set.
        """
        return self.env.str("INPUT_COMMIT_AUTHOR")

    def get_commit_email(self) -> str:
        """Get the Git commit author email.

        Returns:
            The email address to use for commits.

        Raises:
            environs.EnvError: If INPUT_COMMIT_EMAIL is not set.
        """
        return self.env.str("INPUT_COMMIT_EMAIL")

    def get_chart_name(self) -> str:
        """Get and validate the Helm chart name.

        The chart name is validated to prevent command injection attacks.
        Valid chart names must start with an alphanumeric character and
        contain only alphanumeric characters, dashes, and underscores.

        Returns:
            The validated chart name.

        Raises:
            environs.EnvError: If INPUT_CHART_NAME is not set.
            ValueError: If the chart name contains invalid characters.
        """
        name = self.env.str("INPUT_CHART_NAME")
        if not CHART_NAME_PATTERN.match(name):
            raise ValueError(
                f"Invalid chart name: '{name}'. "
                "Chart names must start with an alphanumeric character and "
                "contain only alphanumeric characters, dashes (-), and underscores (_)."
            )
        return name

    def get_charts_path(self) -> str:
        """Get the path to the charts directory within the repository.

        Returns:
            The relative path to the charts directory.

        Raises:
            environs.EnvError: If INPUT_CHARTS_PATH is not set.
        """
        return self.env.str("INPUT_CHARTS_PATH")

    def get_app_version(self) -> str:
        """Get the new application version to set.

        Returns:
            The new appVersion value for the chart.

        Raises:
            environs.EnvError: If INPUT_APP_VERSION is not set.
        """
        return self.env.str("INPUT_APP_VERSION")

    def generate_docs(self) -> bool:
        """Check if helm-docs should be run to generate documentation.

        Returns:
            True if helm-docs should be run, False otherwise.
            Defaults to False when not running under GitHub Actions.
        """
        return self.env.bool("INPUT_GENERATE_DOCS", False)

    def update_readme(self) -> bool:
        """Check if the README should be updated with a charts table.

        Returns:
            True if README should be updated, False otherwise.
            Defaults to False when not running under GitHub Actions.
        """
        return self.env.bool("INPUT_UPDATE_README", False)

    def update_chart_annotations(self) -> bool:
        """Check if chart annotations should be updated.

        Returns:
            True if annotations should be updated, False otherwise.
            Defaults to False when not running under GitHub Actions.
        """
        return self.env.bool("INPUT_UPDATE_CHART_ANNOTATIONS", False)
