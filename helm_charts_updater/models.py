from typing import Optional

import semver
from pydantic import BaseModel
from pydantic import validator


class Chart(BaseModel):
    name: str
    description: str
    version: str
    appVersion: Optional[str] = None

    @validator("version", pre=True)
    def validate_version(cls, v) -> Optional[str]:
        if semver.VersionInfo.isvalid(v):
            return v
        else:
            raise ValueError(f"{v} is not a valid version")
