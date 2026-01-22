"""Tests for Pydantic models."""

from typing import Any

import pytest
from pydantic import ValidationError

from helm_charts_updater.models import Chart
from helm_charts_updater.models import Dependency
from helm_charts_updater.models import Maintainer


class TestMaintainer:
    """Tests for Maintainer model."""

    def test_valid_maintainer_all_fields(self) -> None:
        """Test creating a maintainer with all fields."""
        maintainer = Maintainer(
            name="Test User", email="test@example.com", url="https://github.com/test"
        )
        assert maintainer.name == "Test User"
        assert maintainer.email == "test@example.com"
        assert maintainer.url == "https://github.com/test"

    def test_maintainer_required_name_only(self) -> None:
        """Test maintainer with only required name field."""
        maintainer = Maintainer(name="Test User")
        assert maintainer.name == "Test User"
        assert maintainer.email is None
        assert maintainer.url is None

    def test_maintainer_missing_name_fails(self) -> None:
        """Test that missing name raises ValidationError."""
        with pytest.raises(ValidationError):
            Maintainer()  # type: ignore[call-arg]


class TestDependency:
    """Tests for Dependency model."""

    def test_valid_dependency_all_fields(self) -> None:
        """Test creating a dependency with all fields."""
        dep = Dependency(
            name="postgresql",
            version="12.0.0",
            repository="https://charts.bitnami.com/bitnami",
            condition="postgresql.enabled",
            tags=["database"],
            alias="db",
        )
        assert dep.name == "postgresql"
        assert dep.version == "12.0.0"
        assert dep.repository == "https://charts.bitnami.com/bitnami"
        assert dep.condition == "postgresql.enabled"
        assert dep.tags == ["database"]
        assert dep.alias == "db"

    def test_dependency_required_fields_only(self) -> None:
        """Test dependency with only required fields."""
        dep = Dependency(name="redis", version="1.0.0")
        assert dep.name == "redis"
        assert dep.version == "1.0.0"
        assert dep.repository is None

    def test_invalid_dependency_version_rejected(self) -> None:
        """Test that invalid dependency versions are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Dependency(name="test", version="not-semver")

        assert "not a valid semver range" in str(exc_info.value)

    @pytest.mark.parametrize(
        "version",
        [
            # Strict versions
            "1.0.0",
            "2.3.4",
            "0.0.1",
            "10.20.30",
            "1.0.0-alpha",
            "1.0.0-beta.1",
            "1.0.0+build",
            # Semver ranges (Helm dependency format)
            "^1.0.0",
            "~2.3.4",
            ">=1.0.0",
            ">=1.0.0 <2.0.0",
            "1.x",
            "1.*",
            "*",
        ],
    )
    def test_valid_dependency_versions(self, version: str) -> None:
        """Test that valid semver versions and ranges are accepted."""
        dep = Dependency(name="test", version=version)
        assert dep.version == version


class TestChart:
    """Tests for Chart model."""

    def test_valid_chart_all_fields(self, sample_chart_data: dict[str, Any]) -> None:
        """Test creating a chart with all common fields."""
        chart = Chart(**sample_chart_data)
        assert chart.name == "test-chart"
        assert chart.description == "A test Helm chart"
        assert chart.version == "1.0.0"
        assert chart.appVersion == "1.0.0"
        assert chart.type == "application"

    def test_chart_required_fields_only(self) -> None:
        """Test chart with only required fields."""
        chart = Chart(
            name="minimal-chart",
            description="Minimal chart",
            version="1.0.0",
        )
        assert chart.name == "minimal-chart"
        assert chart.version == "1.0.0"
        assert chart.appVersion is None
        assert chart.type is None

    def test_invalid_chart_version_rejected(self) -> None:
        """Test that invalid chart versions are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Chart(
                name="test-chart",
                description="A test chart",
                version="invalid-version",
            )

        assert "not a valid semantic version" in str(exc_info.value)

    def test_chart_with_maintainers(self) -> None:
        """Test chart with maintainers list."""
        chart = Chart(
            name="test-chart",
            description="Test chart",
            version="1.0.0",
            maintainers=[
                {"name": "User 1", "email": "user1@example.com"},
                {"name": "User 2"},
            ],
        )
        assert len(chart.maintainers) == 2
        assert chart.maintainers[0].name == "User 1"
        assert chart.maintainers[1].email is None

    def test_chart_with_dependencies(self) -> None:
        """Test chart with dependencies list."""
        chart = Chart(
            name="test-chart",
            description="Test chart",
            version="1.0.0",
            dependencies=[
                {"name": "postgresql", "version": "12.0.0"},
                {"name": "redis", "version": "1.0.0"},
            ],
        )
        assert len(chart.dependencies) == 2
        assert chart.dependencies[0].name == "postgresql"

    def test_chart_with_annotations(self) -> None:
        """Test chart with annotations dictionary."""
        chart = Chart(
            name="test-chart",
            description="Test chart",
            version="1.0.0",
            annotations={
                "artifacthub.io/changes": "- Initial release",
                "custom/annotation": "value",
            },
        )
        assert chart.annotations is not None
        assert "artifacthub.io/changes" in chart.annotations

    def test_model_dump_excludes_none(self) -> None:
        """Test that model_dump with exclude_none works correctly."""
        chart = Chart(
            name="test-chart",
            description="Test chart",
            version="1.0.0",
        )
        data = chart.model_dump(exclude_none=True)

        assert "name" in data
        assert "version" in data
        assert "type" not in data  # None values excluded
        assert "appVersion" not in data

    def test_model_dump_includes_all(self) -> None:
        """Test that model_dump without exclude_none includes None values."""
        chart = Chart(
            name="test-chart",
            description="Test chart",
            version="1.0.0",
        )
        data = chart.model_dump()

        assert "name" in data
        assert "type" in data  # None values included
        assert data["type"] is None

    @pytest.mark.parametrize(
        "version",
        [
            "1.0.0",
            "2.3.4",
            "0.0.1",
            "10.20.30",
        ],
    )
    def test_valid_chart_versions(self, version: str) -> None:
        """Test that valid semver versions are accepted."""
        chart = Chart(
            name="test-chart",
            description="Test chart",
            version=version,
        )
        assert chart.version == version
