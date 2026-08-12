import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.finding import Finding
from app.models.repository import Repository


class FindingService:
    @staticmethod
    def get_findings_for_user(
        db: Session,
        user_id: uuid.UUID,
        repository_id: Optional[str] = None,
        severity: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Finding]:
        # Ensure user_id is a UUID object
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        query = (
            select(Finding)
            .join(Repository, Finding.repository_id == Repository.id)
            .where(Repository.user_id == user_id)
        )

        if repository_id:
            if isinstance(repository_id, str):
                repository_id = uuid.UUID(repository_id)
            query = query.where(Finding.repository_id == repository_id)
        if severity:
            query = query.where(Finding.severity == severity)
        if type:
            query = query.where(Finding.type == type)
        if status:
            query = query.where(Finding.status == status)

        return db.scalars(query.order_by(Finding.created_at.desc())).all()

    @staticmethod
    def get_finding(db: Session, finding_id: str, user_id: uuid.UUID) -> Optional[Finding]:
        if isinstance(finding_id, str):
            finding_id = uuid.UUID(finding_id)
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        return db.scalar(
            select(Finding)
            .join(Repository, Finding.repository_id == Repository.id)
            .where(Finding.id == finding_id, Repository.user_id == user_id)
        )

    @staticmethod
    def get_findings_by_scan(db: Session, scan_id: str, user_id: uuid.UUID) -> List[Finding]:
        if isinstance(scan_id, str):
            scan_id = uuid.UUID(scan_id)
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        return db.scalars(
            select(Finding)
            .join(Repository, Finding.repository_id == Repository.id)
            .where(Finding.scan_id == scan_id, Repository.user_id == user_id)
            .order_by(Finding.created_at.desc())
        ).all()

    @staticmethod
    def get_counts_for_user(db: Session, user_id: uuid.UUID) -> dict:
        """Returns open and critical finding counts for the dashboard."""
        open_count = db.scalar(
            select(Finding)
            .join(Repository, Finding.repository_id == Repository.id)
            .where(Repository.user_id == user_id, Finding.status == "OPEN")
        )
        return {
            "open_findings": db.query(Finding).join(Repository).filter(
                Repository.user_id == user_id, Finding.status == "OPEN"
            ).count(),
            "critical_findings": db.query(Finding).join(Repository).filter(
                Repository.user_id == user_id,
                Finding.status == "OPEN",
                Finding.severity == "CRITICAL"
            ).count()
        }
