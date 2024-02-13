from typing import List
from typing import Optional

import semver
from pydantic import BaseModel
from pydantic import field_validator


class Maintainer(BaseModel):
    name: str
    email: Optional[str] = None
    url: Optional[str] = None


class Dependency(BaseModel):
    name: str
    version: str
    repository: Optional[str] = None
    condition: Optional[str] = None
    tags: Optional[List[str]] = None
    importValues: Optional[List[str]] = None
    alias: Optional[str] = None

    @field_validator("version", mode="before")
    def validate_version(cls, v) -> Optional[str]:
        if not semver.VersionInfo.is_valid(v):
            raise ValueError(f"{v} is not a valid version")
        return v


class Chart(BaseModel):
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
    annotations: Optional[dict] = None

    @field_validator("version", mode="before")
    def validate_version(cls, v) -> Optional[str]:
        if not semver.VersionInfo.is_valid(v):
            raise ValueError(f"{v} is not a valid version")
        return v
