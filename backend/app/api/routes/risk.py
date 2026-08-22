import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.risk_service import RiskService
from app.schemas.risk import RiskAssessmentResponse, RepositoryRecalculateResponse, RiskFactorsSchema

router = APIRouter(tags=["Risk Engine"])


def _format_risk_response(assessment) -> RiskAssessmentResponse:
    return RiskAssessmentResponse(
        id=assessment.id,
        finding_id=assessment.finding_id,
        risk_score=assessment.risk_score,
        risk_level=assessment.risk_level,
        priority=assessment.priority,
        factors=RiskFactorsSchema(
            severity=assessment.severity_factor,
            exploitability=assessment.exploitability_factor,
            exposure=assessment.exposure_factor,
            asset_criticality=assessment.asset_criticality_factor,
            confidence=assessment.confidence_factor,
        ),
        explanation=assessment.explanation,
        recommended_action=assessment.recommended_action,
    )


@router.get("/findings/{finding_id}/risk", response_model=RiskAssessmentResponse)
def get_finding_risk(
    finding_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the risk assessment for a specific finding."""
    assessment = RiskService.get_risk_assessment_for_finding(db, finding_id, current_user.id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk assessment not found or you don't have access."
        )
    return _format_risk_response(assessment)


@router.post("/findings/{finding_id}/risk/recalculate", response_model=RiskAssessmentResponse)
def recalculate_finding_risk(
    finding_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recalculate the risk assessment for a specific finding."""
    assessment = RiskService.recalculate_finding_risk(db, finding_id, current_user.id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found or you don't have access."
        )
    return _format_risk_response(assessment)


@router.post("/repositories/{repository_id}/risk/recalculate", response_model=RepositoryRecalculateResponse)
def recalculate_repository_risks(
    repository_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recalculate risk assessments for all findings in a repository."""
    res = RiskService.recalculate_repository_risks(db, repository_id, current_user.id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found or you don't have access."
        )
    return res
