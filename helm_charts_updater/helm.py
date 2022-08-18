import logging
from subprocess import DEVNULL
from subprocess import STDOUT
from subprocess import check_call

import semver
import yaml
from pydantic import ValidationError

from helm_charts_updater import config
from helm_charts_updater.models import Chart


class HelmChart:
    def __init__(self):
        self.charts_path = "charts"
        self.chart_name = config.get_chart_name()
        self.app_version = config.get_app_version()

    def parse_charts_yaml(self) -> Chart:
        logging.info(f"Parsing {self.chart_name}'s Chart.yaml...")

        with open(f"charts/{self.charts_path}/{self.chart_name}/Chart.yaml", "r") as f:
            chart = f.read()

        try:
            return Chart(**yaml.safe_load(chart))
        except ValidationError as err:
            logging.error(err)
            exit(1)

    def update_chart_version(self) -> tuple:
        chart = self.parse_charts_yaml()

        chart_version = semver.bump_patch(chart.version)
        app_version = self.app_version
        old_app_version = chart.appVersion

        if app_version == old_app_version:
            logging.info(
                f"No need to update {self.chart_name} chart version. Skipping..."
            )
            exit(0)

        logging.info(f"Bumping chart version from {chart.version} to {chart_version}")
        chart.version = semver.bump_patch(chart.version)

        logging.info(f"Bumping app version from {chart.appVersion} to {app_version}")
        chart.appVersion = self.app_version

        with open(f"charts/{self.charts_path}/{self.chart_name}/Chart.yaml", "w") as f:
            yaml.safe_dump(chart.dict(exclude_none=True), sort_keys=False, stream=f)

        return chart_version, old_app_version

    def run_helm_docs(self):
        logging.info("Generating helm readme...")

        check_call(
            ["helm-docs", "-c", f"charts/{self.charts_path}/{self.chart_name}"],
            stdout=DEVNULL,
            stderr=STDOUT,
        )
