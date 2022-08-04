from helm_charts_updater.git import GitRepository
from helm_charts_updater.helm import HelmChart


def main():
    repo = GitRepository()
    repo.clone()

    chart = HelmChart()
    chart_version, old_version = chart.update_chart_version()
    chart.run_helm_docs()

    repo.push_changes(chart_version=chart_version,
                      app_name=chart.chart_name,
                      version=chart.app_version,
                      old_version=old_version)


if __name__ == "__main__":
    main()
