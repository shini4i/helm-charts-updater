"""Main entry point for helm-charts-updater.

This module provides the main function that orchestrates the helm chart
update workflow.
"""

from helm_charts_updater import config
from helm_charts_updater.git import GitRepository
from helm_charts_updater.helm import HelmChart
from helm_charts_updater.readme_generator import Readme


def main() -> None:
    """Execute the helm charts update workflow.

    This function orchestrates the complete workflow:
    1. Clone the charts repository
    2. Update the chart version and appVersion
    3. Optionally generate helm-docs documentation
    4. Optionally update the README with a charts table
    5. Commit and push the changes
    """
    repo = GitRepository()

    chart = HelmChart()
    chart_version, old_version = chart.update_chart_version()

    if config.generate_docs():
        chart.run_helm_docs()

    if config.update_readme():
        readme = Readme()
        readme.update_readme(charts=repo.get_charts_list())

    repo.push_changes(
        chart_version=chart_version,
        app_name=chart.chart_name,
        version=chart.app_version,
        old_version=old_version,
    )


if __name__ == "__main__":
    main()
