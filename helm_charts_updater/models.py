"""Pydantic models for Helm chart metadata.

This module defines the data models used to parse and validate
Helm Chart.yaml files.
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import semver
from pydantic import BaseModel
from pydantic import field_validator


class Maintainer(BaseModel):
    """Model representing a Helm chart maintainer.

    Attributes:
        name: The maintainer's name.
        email: Optional email address.
        url: Optional URL (e.g., GitHub profile).
    """

    name: str
    email: Optional[str] = None
    url: Optional[str] = None


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
    repository: Optional[str] = None
    condition: Optional[str] = None
    tags: Optional[List[str]] = None
    importValues: Optional[List[str]] = None
    alias: Optional[str] = None

    @field_validator("version", mode="before")
    @classmethod
    def validate_version(cls, v: Any) -> str:
        """Validate that the version is a valid semver string.

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

    apiVersion: Optional[str] = None
    name: str
    description: str
    type: Optional[str] = None
    sources: Optional[List[str]] = None
    version: str
    keywords: Optional[List[str]] = None
    kubeVersion: Optional[str] = None
    appVersion: Optional[str] = None
    maintainers: Optional[List[Maintainer]] = None
    dependencies: Optional[List[Dependency]] = None
    icon: Optional[str] = None
    annotations: Optional[Dict[str, Any]] = None

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
