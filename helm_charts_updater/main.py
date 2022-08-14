from helm_charts_updater import config
from helm_charts_updater.git import GitRepository
from helm_charts_updater.helm import HelmChart
from helm_charts_updater.readme_generator import Readme


def main():
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
