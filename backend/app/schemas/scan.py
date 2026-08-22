from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class ScanResponse(BaseModel):
    id: UUID
    repository_id: UUID
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    total_findings: int
    scan_summary: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
