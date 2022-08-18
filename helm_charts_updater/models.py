from typing import List
from typing import Optional

import semver
from pydantic import BaseModel
from pydantic import Field
from pydantic import validator


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


class Chart(BaseModel):
    apiVersion: Optional[str]
    name: str
    description: str
    type: Optional[str]
    sources: Optional[List[str]]
    version: str
    kubeVersion: Optional[str]
    appVersion: Optional[str]
    maintainers: Optional[List[Maintainer]]
    dependencies: Optional[List[Dependency]]
    icon: Optional[str]
    annotations: Optional[dict]

    @validator("version", pre=True)
    def validate_version(cls, v) -> Optional[str]:
        if semver.VersionInfo.isvalid(v):
            return v
        else:
            raise ValueError(f"{v} is not a valid version")

    @validator("dependencies", pre=True)
    def validate_dependency_version(cls, v) -> Optional[List[Dependency]]:
        for dependency in v:
            if not semver.VersionInfo.isvalid(dependency["version"]):
                raise ValueError(f"{dependency['version']} is not a valid version")
        return v
