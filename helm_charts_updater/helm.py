import os

import semver
import yaml

from helm_charts_updater import config
from helm_charts_updater.models import Chart


class HelmChart:
    def __init__(self):
        self.charts_path = "charts"
        self.chart_name = config.get_chart_name()
        self.app_version = config.get_app_version()

    def parse_charts_yaml(self) -> Chart:
        print(f"===> Parsing {self.chart_name}'s Chart.yaml...")
        with open(f"charts/{self.charts_path}/{self.chart_name}/Chart.yaml", "r") as f:
            chart = f.read()
        return Chart(**yaml.safe_load(chart))

    def update_chart_version(self) -> tuple:
        chart = self.parse_charts_yaml()

        chart_version = semver.bump_patch(chart.version)
        app_version = self.app_version
        old_app_version = chart.appVersion

        if app_version == old_app_version:
            print(
                f"===> No need to update {self.chart_name} chart version. Skipping..."
            )
            exit(0)

        print(f"===> Bumping chart version from {chart.version} to {chart_version}")
        chart.version = semver.bump_patch(chart.version)

        print(f"===> Bumping app version from {chart.appVersion} to {app_version}")
        chart.appVersion = self.app_version

        with open(f"charts/{self.charts_path}/{self.chart_name}/Chart.yaml", "w") as f:
            yaml.safe_dump(chart.dict(exclude_none=True), sort_keys=False, stream=f)

        return chart_version, old_app_version

    def run_helm_docs(self):
        print("===> Generating helm readme...")
        os.chdir(f"charts/{self.charts_path}/{self.chart_name}")
        os.system("helm-docs .")
        os.chdir("../../..")
