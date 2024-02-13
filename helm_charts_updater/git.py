import logging
import os
import sys
from pathlib import Path

from git import GitCommandError
from git import Repo
from pydantic import ValidationError
from ruamel.yaml import YAML

from helm_charts_updater import config
from helm_charts_updater.models import Chart


class GitRepository:
    def __init__(self):
        self.repo = self._generate_repo_url()
        self.clone_path = config.get_clone_path()

        self.commit_author = config.get_commit_author()
        self.committer_email = config.get_commit_email()

        self.yaml = YAML(typ="safe")

        self._clone()
        self.local_repo = Repo(self.clone_path)

    @staticmethod
    def _generate_repo_url() -> str:
        gh_token = config.get_github_token()
        gh_user = config.get_github_user()
        gh_repo = config.get_github_repo()

        return f"https://{gh_token}@github.com/{gh_user}/{gh_repo}.git"

    def _clone(self):
        if not os.path.exists(self.clone_path):
            logging.info(f"Cloning helm charts repository to {self.clone_path}...")
            Repo.clone_from(self.repo, self.clone_path)
            return
        raise FileExistsError(f"{self.clone_path} already exists, this is unexpected")

    def _commit_changes(self, commit_message):
        self.local_repo.git.add(A=True)
        self.local_repo.git.config("user.name", self.commit_author)
        self.local_repo.git.config("user.email", self.committer_email)
        self.local_repo.index.commit(commit_message)

    def push_changes(self, chart_version, app_name: str, version: str, old_version: str):
        logging.info("Committing changes...")
        commit_message = (
            f"Bump {app_name} chart to {chart_version}\n" f"appVersion {old_version} → {version}"
        )

        self._commit_changes(commit_message)
        origin = self.local_repo.remote(name="origin")

        try:
            origin.push()
        except GitCommandError as error:
            logging.error("Failed to push changes: %s", error)
            if "Updates were rejected" in str(error):
                logging.info("Pulling changes with rebase and retrying push...")
                self.pull_with_rebase()
                origin.push()

    def pull_with_rebase(self):
        logging.info("Pulling latest changes from the remote repo with rebase...")
        origin = self.local_repo.remote(name="origin")
        try:
            self.local_repo.git.pull(
                origin, self.local_repo.active_branch.name, strategy_option="ours", rebase=True
            )
        except GitCommandError as e:
            logging.error("Error while pulling with rebase: %s", e)
            raise GitCommandError

    def get_charts_list(self) -> list:
        logging.info("Getting charts list...")

        charts = []

        for chart in Path(self.clone_path).rglob("Chart.yaml"):
            # We want to avoid including dependencies
            # in the resulting Charts list
            if len(str(chart).split("/")) <= 4:
                with open(chart, "r") as file:
                    try:
                        charts.append(Chart(**self.yaml.load(file)))
                    except ValidationError as err:
                        logging.error(err)
                        sys.exit(1)

        return charts
