from environs import Env


class Config:
    def __init__(self):
        self.env = Env()

    def get_github_token(self):
        return self.env("INPUT_GITHUB_TOKEN")

    def get_github_user(self):
        return self.env("INPUT_GH_USER")

    def get_github_repo(self):
        return self.env("INPUT_GH_REPO")

    def get_clone_path(self):
        return self.env("INPUT_CLONE_PATH")

    def get_commit_author(self):
        return self.env("INPUT_COMMIT_AUTHOR")

    def get_commit_email(self):
        return self.env("INPUT_COMMIT_EMAIL")

    def get_chart_name(self):
        return self.env("INPUT_CHART_NAME")

    def get_charts_path(self):
        return self.env("INPUT_CHARTS_PATH")

    def get_app_version(self):
        return self.env("INPUT_APP_VERSION")

    def generate_docs(self):
        return self.env.bool("INPUT_GENERATE_DOCS")

    def update_readme(self):
        return self.env.bool("INPUT_UPDATE_README")

    def update_chart_annotations(self):
        return self.env.bool("INPUT_UPDATE_CHART_ANNOTATIONS")
