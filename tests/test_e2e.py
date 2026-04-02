"""End-to-end tests for helm-charts-updater.

These tests exercise the full workflow with real git operations
against a local bare repository, real filesystem I/O, and real
Chart.yaml parsing/modification.
"""

import os
import shutil
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from git import Repo
from ruamel.yaml import YAML

from helm_charts_updater.exceptions import ChartValidationError
from helm_charts_updater.main import main

CHART_YAML_CONTENT = """\
apiVersion: v2
name: test-chart
description: A test Helm chart
type: application
version: 1.0.0
appVersion: "1.0.0"
maintainers:
  - name: Test Maintainer
    email: test@example.com
"""

INVALID_CHART_YAML_CONTENT = """\
apiVersion: v2
name: bad-chart
description: Missing version field
"""

VALUES_YAML_CONTENT = """\
# Default values for test-chart
replicaCount: 1

image:
  repository: nginx
  tag: latest
"""

README_WITH_MARKERS = """\
# Charts Repository

<!-- table_start -->
| old content |
<!-- table_end -->

## Footer
"""


@pytest.fixture
def bare_repo(tmp_path: Path) -> Path:
    """Create a bare git repository with initial chart content.

    Sets up a local bare repo that acts as the 'remote' GitHub repository.
    Pre-populates it with a valid Chart.yaml under charts/test-chart/.

    Returns:
        Path to the bare git repository.
    """
    bare_path = tmp_path / "remote.git"
    Repo.init(bare_path, bare=True)

    setup_path = tmp_path / "setup-clone"
    repo = Repo.clone_from(str(bare_path), str(setup_path))

    chart_dir = setup_path / "charts" / "test-chart"
    chart_dir.mkdir(parents=True)
    (chart_dir / "Chart.yaml").write_text(CHART_YAML_CONTENT)
    (chart_dir / "values.yaml").write_text(VALUES_YAML_CONTENT)
    (setup_path / "README.md").write_text(README_WITH_MARKERS)

    repo.git.add(A=True)
    repo.git.config("user.name", "Setup")
    repo.git.config("user.email", "setup@test.com")
    repo.index.commit("Initial chart content")
    repo.remote("origin").push()

    # Clean up the setup clone — only the bare repo matters
    shutil.rmtree(setup_path)

    return bare_path


@pytest.fixture
def e2e_env(tmp_path: Path, bare_repo: Path) -> Generator[dict[str, Any], None, None]:
    """Set up environment variables and patch URL generation for e2e tests.

    Args:
        tmp_path: Pytest temporary directory.
        bare_repo: Path to the bare git repository fixture.

    Yields:
        Dictionary with 'clone_path' and 'bare_repo' paths for assertions.
    """
    clone_path = tmp_path / "work-clone"

    env_vars = {
        "INPUT_GITHUB_TOKEN": "fake-token",
        "INPUT_GH_USER": "fake-user",
        "INPUT_GH_REPO": "fake-repo",
        "INPUT_CLONE_PATH": str(clone_path),
        "INPUT_COMMIT_AUTHOR": "E2E Test",
        "INPUT_COMMIT_EMAIL": "e2e@test.com",
        "INPUT_CHART_NAME": "test-chart",
        "INPUT_CHARTS_PATH": "charts",
        "INPUT_APP_VERSION": "2.0.0",
        "INPUT_GENERATE_DOCS": "false",
        "INPUT_UPDATE_README": "false",
        "INPUT_UPDATE_CHART_ANNOTATIONS": "false",
    }

    repo_url = f"file://{bare_repo}"

    with (
        patch.dict(os.environ, env_vars, clear=False),
        patch(
            "helm_charts_updater.git.GitRepository._generate_repo_url",
            return_value=repo_url,
        ),
    ):
        yield {"clone_path": clone_path, "bare_repo": bare_repo}


def _clone_and_read_chart(bare_repo: Path, dest: Path) -> dict[str, Any]:
    """Clone the bare repo and read the test-chart's Chart.yaml.

    Args:
        bare_repo: Path to the bare git repository.
        dest: Path to clone into.

    Returns:
        Parsed Chart.yaml as a dictionary.
    """
    Repo.clone_from(f"file://{bare_repo}", str(dest))
    chart_path = dest / "charts" / "test-chart" / "Chart.yaml"
    yaml = YAML(typ="safe")
    with open(chart_path, encoding="utf-8") as f:
        return yaml.load(f)


@pytest.mark.e2e
class TestE2EWorkflow:
    """End-to-end tests exercising the full main() workflow."""

    def test_basic_chart_update(self, e2e_env: dict[str, Any]) -> None:
        """Test basic workflow: clone -> update chart -> commit -> push."""
        main()

        # Verify by cloning the bare repo and inspecting the result
        verify_path = Path(e2e_env["clone_path"]).parent / "verify-clone"
        chart_data = _clone_and_read_chart(e2e_env["bare_repo"], verify_path)

        assert chart_data["version"] == "1.0.1"
        assert chart_data["appVersion"] == "2.0.0"

        # Verify commit message format
        repo = Repo(verify_path)
        last_commit = repo.head.commit
        assert "Bump test-chart chart to 1.0.1" in last_commit.message
        assert "appVersion 1.0.0 -> 2.0.0" in last_commit.message

    def test_with_readme_update(self, e2e_env: dict[str, Any]) -> None:
        """Test workflow with README table update enabled."""
        with patch.dict(os.environ, {"INPUT_UPDATE_README": "true"}):
            main()

        verify_path = Path(e2e_env["clone_path"]).parent / "verify-clone"
        Repo.clone_from(f"file://{e2e_env['bare_repo']}", str(verify_path))

        readme_content = (verify_path / "README.md").read_text()

        assert "<!-- table_start -->" in readme_content
        assert "<!-- table_end -->" in readme_content
        assert "test-chart" in readme_content
        assert "1.0.1" in readme_content

    def test_with_chart_annotations(self, e2e_env: dict[str, Any]) -> None:
        """Test workflow with chart annotations update enabled."""
        with patch.dict(os.environ, {"INPUT_UPDATE_CHART_ANNOTATIONS": "true"}):
            main()

        verify_path = Path(e2e_env["clone_path"]).parent / "verify-clone"
        Repo.clone_from(f"file://{e2e_env['bare_repo']}", str(verify_path))

        chart_path = verify_path / "charts" / "test-chart" / "Chart.yaml"
        yaml = YAML(typ="rt")
        with open(chart_path, encoding="utf-8") as f:
            chart_data = yaml.load(f)

        assert "annotations" in chart_data
        changelog = str(chart_data["annotations"]["artifacthub.io/changes"])
        assert "Update test-chart" in changelog
        assert "1.0.0" in changelog
        assert "2.0.0" in changelog

    def test_no_update_needed(self, e2e_env: dict[str, Any]) -> None:
        """Test that same appVersion causes clean return without push."""
        with patch.dict(os.environ, {"INPUT_APP_VERSION": "1.0.0"}):
            main()

        # Verify no new commit was pushed to the bare repo
        verify_path = Path(e2e_env["clone_path"]).parent / "verify-clone"
        Repo.clone_from(f"file://{e2e_env['bare_repo']}", str(verify_path))
        repo = Repo(verify_path)
        commits = list(repo.iter_commits())
        assert len(commits) == 1
        assert commits[0].message.startswith("Initial chart content")

    def test_invalid_chart_yaml(self, tmp_path: Path) -> None:
        """Test that invalid Chart.yaml raises ChartValidationError."""
        bare_path = tmp_path / "invalid-remote.git"
        Repo.init(bare_path, bare=True)

        setup_path = tmp_path / "invalid-setup"
        repo = Repo.clone_from(str(bare_path), str(setup_path))

        chart_dir = setup_path / "charts" / "bad-chart"
        chart_dir.mkdir(parents=True)
        (chart_dir / "Chart.yaml").write_text(INVALID_CHART_YAML_CONTENT)

        repo.git.add(A=True)
        repo.git.config("user.name", "Setup")
        repo.git.config("user.email", "setup@test.com")
        repo.index.commit("Invalid chart")
        repo.remote("origin").push()
        shutil.rmtree(setup_path)

        clone_path = tmp_path / "invalid-clone"
        env_vars = {
            "INPUT_GITHUB_TOKEN": "fake",
            "INPUT_GH_USER": "fake",
            "INPUT_GH_REPO": "fake",
            "INPUT_CLONE_PATH": str(clone_path),
            "INPUT_COMMIT_AUTHOR": "Test",
            "INPUT_COMMIT_EMAIL": "t@t.com",
            "INPUT_CHART_NAME": "bad-chart",
            "INPUT_CHARTS_PATH": "charts",
            "INPUT_APP_VERSION": "2.0.0",
            "INPUT_GENERATE_DOCS": "false",
            "INPUT_UPDATE_README": "false",
            "INPUT_UPDATE_CHART_ANNOTATIONS": "false",
        }

        with (
            patch.dict(os.environ, env_vars, clear=False),
            patch(
                "helm_charts_updater.git.GitRepository._generate_repo_url",
                return_value=f"file://{bare_path}",
            ),
            pytest.raises(ChartValidationError),
        ):
            main()

    @pytest.mark.skipif(
        shutil.which("helm-docs") is None,
        reason="helm-docs not available in PATH",
    )
    def test_with_helm_docs(self, e2e_env: dict[str, Any]) -> None:
        """Test workflow with helm-docs generation enabled."""
        with patch.dict(os.environ, {"INPUT_GENERATE_DOCS": "true"}):
            main()

        # Verify helm-docs produced a README.md in the chart directory
        clone_path = Path(e2e_env["clone_path"])
        chart_readme = clone_path / "charts" / "test-chart" / "README.md"
        assert chart_readme.exists(), "helm-docs should have generated a chart README.md"
