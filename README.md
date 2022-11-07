<div align="center">

# helm-charts-updater

A tool that will update helm charts in a given repository

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/shini4i/helm-charts-updater/Update%20Main%20Version?style=plastic)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/shini4i/helm-charts-updater?style=plastic)
![GitHub](https://img.shields.io/github/license/shini4i/helm-charts-updater?style=plastic)

</div>

## Project Description

> :warning: Currently, only patch version bump is supported for chart version.

The use case is relatively niche. The idea is that there are a lot of helm charts in a single git
repository, and it is required to bump both chart version and appVersion from a pipeline in a different repository.

So it is required that the selected helm chart uses appVersion as an image tag.

Additionally, it can generate helm readme and generate table of the existing charts in the main README.md file.

It might be a good tandem for the [chart-releaser-action](https://github.com/helm/chart-releaser-action).

## Example Workflow

```yaml
- name: Update helm chart
  uses: shini4i/helm-charts-updater@v1
  with:
    github_token: ${{ secrets.GH_TOKEN }}
    gh_user: shini4i
    gh_repo: charts
    chart_name: my-chart
    app_version: ${{ github.ref_name }}

    # Optional. Path to the location of helm charts in the gh_repo
    # Default to charts
    charts_path: charts

    # Optional. Git user.name
    # Defaults to github-actions[bot]
    commit_author: github-actions[bot]

    # Optional. Git user.email
    # Defaults to github-actions[bot]@users.noreply.github.com
    commit_email: github-actions[bot]@users.noreply.github.com

    # Optional. Whether helm docs should be generated for the selected chart.
    # Defaults to true
    generate_docs: true

    # Optional. Whether the README should be updated with the table of existing charts.
    # Defaults to false
    # NOTE: It is required to have the following comments in the README.md file:
    # <!-- table_start -->
    # <!-- table_end -->
    # The table would be generated between those two comments.
    update_readme: true
```
