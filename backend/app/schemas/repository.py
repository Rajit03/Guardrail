import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

# Strict GitHub repository URL pattern. Only https://github.com/{owner}/{repo}
# is accepted — no credentials, ports, query strings, or fragments — so that
# future phases which interact with repositories never receive a URL pointing
# at an internal host (SSRF prevention).
GITHUB_URL_PATTERN = re.compile(
    r'^https://github\.com/'
    r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/'
    r'[A-Za-z0-9._-]{1,100}/?$'
)

BRANCH_NAME_PATTERN = re.compile(r'^[A-Za-z0-9._/-]{1,255}$')


class RepositoryProvider(str, Enum):
    GITHUB = "github"


def validate_repository_url(url: str) -> str:
    url = url.strip()
    if not GITHUB_URL_PATTERN.match(url):
        raise ValueError(
            "Invalid repository URL. Expected format: https://github.com/owner/repository"
        )
    return url.rstrip('/')


def validate_branch_name(branch: str) -> str:
    branch = branch.strip()
    if not BRANCH_NAME_PATTERN.match(branch) or branch.startswith('/') or '..' in branch:
        raise ValueError("Invalid branch name.")
    return branch


class RepositoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Repository display name")
    url: str = Field(..., max_length=500, description="Repository URL")
    provider: RepositoryProvider = Field(
        default=RepositoryProvider.GITHUB,
        description="Repository hosting provider"
    )
    default_branch: str = Field(default="main", min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Repository name cannot be empty.")
        if len(v) > 100:
            raise ValueError("Repository name must be at most 100 characters.")
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        return validate_repository_url(v)

    @field_validator("default_branch")
    @classmethod
    def validate_default_branch(cls, v: str) -> str:
        return validate_branch_name(v)

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v or None


class RepositoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    default_branch: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("Repository name cannot be empty.")
        if len(v) > 100:
            raise ValueError("Repository name must be at most 100 characters.")
        return v

    @field_validator("default_branch")
    @classmethod
    def validate_default_branch(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_branch_name(v)

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return v.strip() or None


class RepositoryOut(BaseModel):
    id: uuid.UUID
    name: str
    url: str
    provider: str
    default_branch: str
    description: Optional[str]
    is_active: bool
    last_scan_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RepositoryListOut(BaseModel):
    repositories: List[RepositoryOut]
