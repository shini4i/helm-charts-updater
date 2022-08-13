import os

from git import Repo


class GitRepository:
    def __init__(self):

        github_token = os.environ.get("INPUT_GITHUB_TOKEN")
        gh_user = os.environ.get("INPUT_GH_USER")
        gh_repo = os.environ.get("INPUT_GH_REPO")

        self.repo = f"https://{github_token}@github.com/{gh_user}/{gh_repo}.git"
        self.repo_path = "charts"

        self.commit_author = "github-actions[bot]"
        self.committer_email = "github-actions[bot]@users.noreply.github.com"

        self._clone()
        self.local_repo = Repo(self.repo_path)

    def _clone(self):
        if not os.path.exists(self.repo_path):
            print(f"===> Cloning helm charts repository to {self.repo_path}...")
            Repo.clone_from(self.repo, self.repo_path)

    def _commit_changes(self, commit_message):
        self.local_repo.git.add(A=True)
        self.local_repo.git.config("user.name", self.commit_author)
        self.local_repo.git.config("user.email", self.committer_email)
        self.local_repo.index.commit(commit_message)

    def push_changes(
        self, chart_version, app_name: str, version: str, old_version: str
    ):
        print("===> Committing changes...")
        commit_message = (
            f"Bump {app_name} chart to {chart_version}\n"
            f"appVersion {old_version} → {version}"
        )

        self._commit_changes(commit_message)
        origin = self.local_repo.remote(name="origin")
        origin.push()
