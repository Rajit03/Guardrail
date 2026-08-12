import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class RepositoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    url: str
    provider: str = Field(default="github")
    default_branch: str = Field(default="main", min_length=1)
    description: Optional[str] = None

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Name cannot be empty')
        return v

    @field_validator('url')
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith("https://github.com/"):
            raise ValueError('URL must be a valid GitHub repository URL')
        parts = v.split("https://github.com/")[1].split("/")
        if len(parts) < 2 or not parts[0] or not parts[1]:
            raise ValueError('URL must follow the pattern https://github.com/owner/repository')
        return v


class RepositoryCreate(RepositoryBase):
    pass


class RepositoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    default_branch: Optional[str] = Field(None, min_length=1)
    is_active: Optional[bool] = None

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Name cannot be empty')
        return v


class RepositoryResponse(RepositoryBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_scan_at: Optional[datetime] = None
    # Computed fields populated by the service layer, not ORM relationships
    findings_count: int = 0
    last_scan_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
