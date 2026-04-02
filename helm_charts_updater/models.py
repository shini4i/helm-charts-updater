"""Pydantic models for Helm chart metadata.

This module defines the data models used to parse and validate
Helm Chart.yaml files.
"""

from typing import Any

# `semver` is used for strict version parsing and bumping (chart versions).
# `semantic_version` (NpmSpec) is used for validating semver ranges in
# Helm dependency version constraints (e.g., "^1.0.0", "~2.3.4", ">=1.0.0 <2.0.0").
import semver
from pydantic import BaseModel
from pydantic import field_validator
from semantic_version import NpmSpec


class Maintainer(BaseModel):
    """Model representing a Helm chart maintainer.

    Attributes:
        name: The maintainer's name.
        email: Optional email address.
        url: Optional URL (e.g., GitHub profile).
    """

    name: str
    email: str | None = None
    url: str | None = None


class Dependency(BaseModel):
    """Model representing a Helm chart dependency.

    Attributes:
        name: The name of the dependency chart.
        version: The semver version constraint.
        repository: The Helm repository URL.
        condition: Optional condition for enabling the dependency.
        tags: Optional tags for grouping dependencies.
        importValues: Optional values to import from the dependency.
        alias: Optional alias for the dependency.
    """

    name: str
    version: str
    repository: str | None = None
    condition: str | None = None
    tags: list[str] | None = None
    importValues: list[str] | None = None
    alias: str | None = None

    @field_validator("version", mode="before")
    @classmethod
    def validate_version(cls, v: Any) -> str:
        """Validate that the version is a valid semver range string.

        Uses NpmSpec to validate semver ranges as used in Helm chart dependencies.

        Args:
            v: The version value to validate.

        Returns:
            The validated version string.

        Raises:
            ValueError: If the version is not a valid semver range.
        """
        try:
            NpmSpec(str(v))
        except ValueError as e:
            raise ValueError(f"{v} is not a valid semver range: {e}") from e
        return str(v)


class Chart(BaseModel):
    """Model representing a Helm Chart.yaml file.

    This model captures all standard fields from a Helm Chart.yaml
    as defined in the Helm chart specification.

    Attributes:
        apiVersion: The chart API version (v1 or v2).
        name: The name of the chart.
        description: A single-sentence description of the chart.
        type: The type of the chart (application or library).
        sources: List of URLs to source code for this project.
        version: The chart version (semver).
        keywords: List of keywords about the project.
        kubeVersion: The Kubernetes version constraint.
        appVersion: The version of the app that this chart deploys.
        maintainers: List of maintainers.
        dependencies: List of chart dependencies.
        icon: URL to an SVG or PNG image for the chart.
        annotations: Additional annotations (key-value pairs).
    """

    apiVersion: str | None = None
    name: str
    description: str
    type: str | None = None
    sources: list[str] | None = None
    version: str
    keywords: list[str] | None = None
    kubeVersion: str | None = None
    appVersion: str | None = None
    maintainers: list[Maintainer] | None = None
    dependencies: list[Dependency] | None = None
    icon: str | None = None
    annotations: dict[str, Any] | None = None

    @field_validator("version", mode="before")
    @classmethod
    def validate_version(cls, v: Any) -> str:
        """Validate that the chart version is a valid semver string.

        Args:
            v: The version value to validate.

        Returns:
            The validated version string.

        Raises:
            ValueError: If the version is not valid semver.
        """
        if not semver.Version.is_valid(str(v)):
            raise ValueError(f"{v} is not a valid semantic version")
        return str(v)
