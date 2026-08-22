from datetime import datetime
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.schemas.risk import RiskAssessmentResponse


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

    # Extended Vulnerability & Package Fields
    package_name: Optional[str] = None
    installed_version: Optional[str] = None
    fixed_version: Optional[str] = None
    vulnerability_id: Optional[str] = None
    aliases: Optional[List[str]] = None

    # Risk Engine Computed/Relational Fields
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    priority: Optional[str] = None
    risk_assessment: Optional[RiskAssessmentResponse] = None

    model_config = ConfigDict(from_attributes=True)


class FindingListResponse(BaseModel):
    findings: List[FindingResponse]
