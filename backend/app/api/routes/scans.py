from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid as uuid_lib

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.repository_service import RepositoryService
from app.services.scan_service import ScanService
from app.services.finding_service import FindingService
from app.schemas.scan import ScanResponse
from app.schemas.finding import FindingResponse, FindingListResponse

router = APIRouter(tags=["Scans"])


@router.post("/repositories/{repository_id}/scan", response_model=ScanResponse)
def scan_repository(
    repository_id: uuid_lib.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger a security scan for a repository. Runs synchronously."""
    service = RepositoryService(db)
    repository = service.get_repository(user_id=current_user.id, repository_id=repository_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found or you don't have access."
        )

    scan = ScanService.run_scan(db, repository)
    return scan


@router.get("/scans/{scan_id}", response_model=ScanResponse)
def get_scan(
    scan_id: uuid_lib.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get scan status by ID."""
    scan = ScanService.get_scan(db, scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")

    # Verify ownership
    service = RepositoryService(db)
    repository = service.get_repository(user_id=current_user.id, repository_id=scan.repository_id)
    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")

    return scan


@router.get("/scans/{scan_id}/findings", response_model=FindingListResponse)
def get_scan_findings(
    scan_id: uuid_lib.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all findings for a specific scan."""
    scan = ScanService.get_scan(db, scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")

    service = RepositoryService(db)
    repository = service.get_repository(user_id=current_user.id, repository_id=scan.repository_id)
    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")

    findings = FindingService.get_findings_by_scan(db, str(scan_id), str(current_user.id))
    return {"findings": findings}
