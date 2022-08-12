<div align="center">

# helm-charts-updater

A tool that will update helm charts in a given repository.

</div>

## Project Description

> The project is still in a testing phase. Some issues might occur.

The use case is relatively niche. The idea is that there are a lot of helm charts in a single git
repository, and it is required to bump both chart version and appVersion. That's all that this automation will do.

So it is required that the selected helm chart uses appVersion as an image tag.

To be used in tandem with the [chart-releaser-action](https://github.com/helm/chart-releaser-action).

## Example Workflow

```bash
- name: Update helm chart
  uses: shini4i/helm-charts-updater@v0.1.2
  with:
    github_token: ${{ secrets.GH_TOKEN }}
    gh_user: shini4i
    gh_repo: charts
    chart_name: my-chart
    app_version: ${{ github.ref_name }}
