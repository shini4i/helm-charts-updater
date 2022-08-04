import os


class GitRepository:
    def __init__(self):

        github_token = os.environ.get("INPUT_GITHUB_TOKEN")
        gh_user = os.environ.get("INPUT_GH_USER")
        gh_repo = os.environ.get("INPUT_GH_REPO")

        self.repo = f"https://{github_token}@github.com/{gh_user}/{gh_repo}.git"
        self.repo_path = "charts"

        self.commit_author = "github-actions[bot]"
        self.committer_email = "github-actions[bot]@users.noreply.github.com"

    def clone(self):
        if not os.path.exists(self.repo_path):
            print(f"===> Cloning helm charts repository to {self.repo_path}...")
            os.system(f"git clone {self.repo} {self.repo_path}")

    def push_changes(self, chart_version, app_name: str, version: str, old_version: str):
        print("===> Committing changes...")
        commit_message = f"Bump {app_name} chart to {chart_version}\n" \
                         f"appVersion {old_version} → {version}"

        os.chdir(self.repo_path)
        os.system(f"git config user.name {self.commit_author}")
        os.system(f"git config user.email {self.committer_email}")
        os.system(f"git add -A")
        os.system(f"git commit -m '{commit_message}'")
        os.system("git push")
