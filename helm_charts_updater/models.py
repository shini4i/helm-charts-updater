from typing import List
from typing import Optional

import semver
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


class Maintainer(BaseModel):
    name: str
    email: Optional[str]
    url: Optional[str]


class Dependency(BaseModel):
    name: str
    version: str
    repository: Optional[str]
    condition: Optional[str]
    tags: Optional[List[str]]
    importValues: Optional[List[str]] = Field(alias="import-values")
    alias: Optional[str]

    @field_validator("version",  mode="before")
    def validate_version(cls, v) -> Optional[str]:
        if not semver.VersionInfo.is_valid(v):
            raise ValueError(f"{v} is not a valid version")
        return v


class Chart(BaseModel):
    apiVersion: Optional[str]
    name: str
    description: str
    type: Optional[str]
    sources: Optional[List[str]]
    version: str
    keywords: Optional[List[str]]
    kubeVersion: Optional[str]
    appVersion: Optional[str]
    maintainers: Optional[List[Maintainer]]
    dependencies: Optional[List[Dependency]]
    icon: Optional[str]
    annotations: Optional[dict]

    @field_validator("version", mode="before")
    def validate_version(cls, v) -> Optional[str]:
        if not semver.VersionInfo.is_valid(v):
            raise ValueError(f"{v} is not a valid version")
        return v
