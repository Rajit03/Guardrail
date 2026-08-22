import uuid
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.finding import Finding
from app.models.repository import Repository


class FindingService:
    @staticmethod
    def get_findings_for_user(
        db: Session,
        user_id: uuid.UUID | str,
        repository_id: Optional[str] = None,
        severity: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Finding]:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        query = (
            select(Finding)
            .join(Repository, Finding.repository_id == Repository.id)
            .where(Repository.user_id == user_id)
        )

        if repository_id:
            try:
                repo_uuid = uuid.UUID(repository_id) if isinstance(repository_id, str) else repository_id
                query = query.where(Finding.repository_id == repo_uuid)
            except ValueError:
                return []

        if severity:
            query = query.where(Finding.severity == severity.upper())
        if type:
            query = query.where(Finding.type == type.upper())
        if status:
            query = query.where(Finding.status == status.upper())

        return list(db.scalars(query.order_by(Finding.created_at.desc())).all())

    @staticmethod
    def get_finding(db: Session, finding_id: uuid.UUID | str, user_id: uuid.UUID | str) -> Optional[Finding]:
        if isinstance(finding_id, str):
            try:
                finding_id = uuid.UUID(finding_id)
            except ValueError:
                return None
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return None

        return db.scalar(
            select(Finding)
            .join(Repository, Finding.repository_id == Repository.id)
            .where(Finding.id == finding_id, Repository.user_id == user_id)
        )

    @staticmethod
    def get_findings_by_scan(db: Session, scan_id: uuid.UUID | str, user_id: uuid.UUID | str) -> List[Finding]:
        if isinstance(scan_id, str):
            try:
                scan_id = uuid.UUID(scan_id)
            except ValueError:
                return []
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return []

        return list(db.scalars(
            select(Finding)
            .join(Repository, Finding.repository_id == Repository.id)
            .where(Finding.scan_id == scan_id, Repository.user_id == user_id)
            .order_by(Finding.created_at.desc())
        ).all())

    @staticmethod
    def get_counts_for_user(db: Session, user_id: uuid.UUID | str) -> Dict[str, int]:
        """Returns open and critical finding counts for the dashboard."""
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        open_count = db.scalar(
            select(func.count())
            .select_from(Finding)
            .join(Repository, Finding.repository_id == Repository.id)
            .where(Repository.user_id == user_id, Finding.status == "OPEN")
        ) or 0

        critical_count = db.scalar(
            select(func.count())
            .select_from(Finding)
            .join(Repository, Finding.repository_id == Repository.id)
            .where(
                Repository.user_id == user_id,
                Finding.status == "OPEN",
                Finding.severity == "CRITICAL"
            )
        ) or 0

        return {
            "open_findings": open_count,
            "critical_findings": critical_count
        }
