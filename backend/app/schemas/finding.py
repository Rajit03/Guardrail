from datetime import datetime
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class FindingResponse(BaseModel):
    id: UUID
    repository_id: UUID
    scan_id: UUID
    type: str
    severity: str
    title: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    scanner: str
    rule_id: Optional[str] = None
    evidence: Optional[str] = None
    recommendation: Optional[str] = None
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class FindingListResponse(BaseModel):
    findings: List[FindingResponse]
