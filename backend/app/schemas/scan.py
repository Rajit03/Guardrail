from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ScanResponse(BaseModel):
    id: UUID
    repository_id: UUID
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_findings: int
    
    model_config = ConfigDict(from_attributes=True)
