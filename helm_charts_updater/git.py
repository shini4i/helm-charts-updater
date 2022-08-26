import logging
import os
from pathlib import Path

import yaml
from git import Repo
from pydantic import ValidationError

from helm_charts_updater import config
from helm_charts_updater.models import Chart


class GitRepository:
    def __init__(self):
        self.repo = self._generate_repo_url()
        self.repo_path = "charts"

        self.commit_author = config.get_commit_author()
        self.committer_email = config.get_commit_email()

        self._clone()
        self.local_repo = Repo(self.repo_path)

    @staticmethod
    def _generate_repo_url() -> str:
        gh_token = config.get_github_token()
        gh_user = config.get_github_user()
        gh_repo = config.get_github_repo()

        return f"https://{gh_token}@github.com/{gh_user}/{gh_repo}.git"

    def _clone(self):
        if not os.path.exists(self.repo_path):
            logging.info(f"Cloning helm charts repository to {self.repo_path}...")
            Repo.clone_from(self.repo, self.repo_path)

    def _commit_changes(self, commit_message):
        self.local_repo.git.add(A=True)
        self.local_repo.git.config("user.name", self.commit_author)
        self.local_repo.git.config("user.email", self.committer_email)
        self.local_repo.index.commit(commit_message)

    def push_changes(
        self, chart_version, app_name: str, version: str, old_version: str
    ):
        logging.info("Committing changes...")
        commit_message = (
            f"Bump {app_name} chart to {chart_version}\n"
            f"appVersion {old_version} → {version}"
        )

        self._commit_changes(commit_message)
        origin = self.local_repo.remote(name="origin")
        origin.push()

    @staticmethod
    def get_charts_list() -> list:
        logging.info("Getting charts list...")

        charts = []

        for chart in Path("charts").rglob("Chart.yaml"):
            # We want to avoid including dependencies
            # in the resulting Charts list
            if len(str(chart).split("/")) <= 4:
                with open(chart, "r") as file:
                    try:
                        charts.append(Chart(**yaml.safe_load(file)))
                    except ValidationError as err:
                        logging.error(err)
                        exit(1)

        return charts
