from uuid import UUID
from typing import Optional, Dict
from pydantic import BaseModel, ConfigDict


class RiskFactorsSchema(BaseModel):
    severity: float
    exploitability: float
    exposure: float
    asset_criticality: float
    confidence: float


class RiskAssessmentResponse(BaseModel):
    id: Optional[UUID] = None
    finding_id: UUID
    risk_score: int
    risk_level: str
    priority: str
    factors: RiskFactorsSchema
    explanation: Optional[str] = None
    recommended_action: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RepositoryRecalculateResponse(BaseModel):
    repository_id: UUID
    findings_processed: int
    assessments_created: int
