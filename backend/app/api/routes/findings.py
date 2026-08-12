from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.finding_service import FindingService
from app.schemas.finding import FindingResponse, FindingListResponse

router = APIRouter(prefix="/findings", tags=["Findings"])


@router.get("", response_model=FindingListResponse)
def list_findings(
    repository_id: Optional[str] = None,
    severity: Optional[str] = None,
    type: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all findings for the authenticated user, with optional filters."""
    findings = FindingService.get_findings_for_user(
        db,
        current_user.id,
        repository_id=repository_id,
        severity=severity,
        type=type,
        status=status_filter
    )
    return {"findings": findings}


@router.get("/{finding_id}", response_model=FindingResponse)
def get_finding(
    finding_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific finding."""
    finding = FindingService.get_finding(db, finding_id, current_user.id)
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found.")
    return finding
