from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    DashboardRepositoriesResponse,
    DashboardFindingsPaginatedResponse,
    DashboardRiskTrendResponse,
)

router = APIRouter(prefix="/dashboard", tags=["Security Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns high-level security overview, overall security score,
    severity distributions, top priority actions, and scanner health
    scoped exclusively to the authenticated user.
    """
    return DashboardService.get_dashboard_summary(db, current_user.id)


@router.get("/repositories", response_model=DashboardRepositoriesResponse)
def get_dashboard_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns connected repositories overview with detected language,
    security score, and severity breakdown for the authenticated user.
    """
    return DashboardService.get_dashboard_repositories(db, current_user.id)


@router.get("/findings", response_model=DashboardFindingsPaginatedResponse)
def get_dashboard_findings(
    repository_id: Optional[str] = None,
    severity: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    scanner: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns paginated, searchable, filterable security findings for the authenticated user.
    """
    return DashboardService.get_dashboard_findings(
        db=db,
        user_id=current_user.id,
        repository_id=repository_id,
        severity=severity,
        type=type,
        status=status,
        scanner=scanner,
        search=search,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
    )


@router.get("/risk-trend", response_model=DashboardRiskTrendResponse)
def get_dashboard_risk_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns historical security scores and finding counts over time based on actual scan history.
    """
    return DashboardService.get_risk_trend(db, current_user.id)
