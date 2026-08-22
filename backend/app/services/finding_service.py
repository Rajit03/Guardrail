import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case, desc, outerjoin

from app.models.finding import Finding
from app.models.repository import Repository
from app.models.risk_assessment import RiskAssessment


def _attach_risk_fields(db: Session, findings: List[Finding]) -> List[Finding]:
    """
    Attaches computed/relational risk_score, risk_level, priority, and risk_assessment
    object to each Finding instance for seamless serialization.
    """
    if not findings:
        return []

    finding_ids = [f.id for f in findings]
    assessments = list(
        db.scalars(
            select(RiskAssessment).where(RiskAssessment.finding_id.in_(finding_ids))
        ).all()
    )
    assessment_map = {a.finding_id: a for a in assessments}

    for f in findings:
        a = assessment_map.get(f.id)
        if a:
            f.risk_score = a.risk_score
            f.risk_level = a.risk_level
            f.priority = a.priority
            f.risk_assessment = a
        else:
            f.risk_score = 0
            f.risk_level = "INFO"
            f.priority = "P3"
            f.risk_assessment = None

    return findings


class FindingService:
    @staticmethod
    def get_findings_for_user(
        db: Session,
        user_id: uuid.UUID | str,
        repository_id: Optional[str] = None,
        severity: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None,
        risk_level: Optional[str] = None,
        priority: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> List[Finding]:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        # Build base query joining Repository and outerjoining RiskAssessment
        query = (
            select(Finding)
            .join(Repository, Finding.repository_id == Repository.id)
            .outerjoin(RiskAssessment, Finding.id == RiskAssessment.finding_id)
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
        if risk_level:
            query = query.where(RiskAssessment.risk_level == risk_level.upper())
        if priority:
            query = query.where(RiskAssessment.priority == priority.upper())

        # Sorting logic
        if sort_by == "risk_score":
            query = query.order_by(desc(RiskAssessment.risk_score), desc(Finding.created_at))
        elif sort_by == "priority":
            priority_order = case(
                (RiskAssessment.priority == "P0", 0),
                (RiskAssessment.priority == "P1", 1),
                (RiskAssessment.priority == "P2", 2),
                (RiskAssessment.priority == "P3", 3),
                else_=4,
            )
            query = query.order_by(priority_order, desc(RiskAssessment.risk_score), desc(Finding.created_at))
        elif sort_by == "severity":
            sev_order = case(
                (Finding.severity == "CRITICAL", 0),
                (Finding.severity == "HIGH", 1),
                (Finding.severity == "MEDIUM", 2),
                (Finding.severity == "LOW", 3),
                else_=4,
            )
            query = query.order_by(sev_order, desc(RiskAssessment.risk_score), desc(Finding.created_at))
        elif sort_by == "created_at":
            query = query.order_by(desc(Finding.created_at))
        else:
            # Default ordering: Priority (P0 -> P3) then Risk Score (desc)
            priority_order = case(
                (RiskAssessment.priority == "P0", 0),
                (RiskAssessment.priority == "P1", 1),
                (RiskAssessment.priority == "P2", 2),
                (RiskAssessment.priority == "P3", 3),
                else_=4,
            )
            query = query.order_by(priority_order, desc(RiskAssessment.risk_score), desc(Finding.created_at))

        findings = list(db.scalars(query).all())
        return _attach_risk_fields(db, findings)

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

        finding = db.scalar(
            select(Finding)
            .join(Repository, Finding.repository_id == Repository.id)
            .where(Finding.id == finding_id, Repository.user_id == user_id)
        )
        if not finding:
            return None

        attached = _attach_risk_fields(db, [finding])
        return attached[0] if attached else finding

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

        findings = list(db.scalars(
            select(Finding)
            .join(Repository, Finding.repository_id == Repository.id)
            .where(Finding.scan_id == scan_id, Repository.user_id == user_id)
            .order_by(Finding.created_at.desc())
        ).all())
        return _attach_risk_fields(db, findings)

    @staticmethod
    def get_risk_summary_for_user(db: Session, user_id: uuid.UUID | str) -> Dict[str, Any]:
        """
        Returns real risk level and priority counts for the user dashboard.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        # Risk level counts for open findings
        levels = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        priorities = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}

        results = db.execute(
            select(RiskAssessment.risk_level, RiskAssessment.priority, func.count(Finding.id))
            .join(Finding, RiskAssessment.finding_id == Finding.id)
            .join(Repository, Finding.repository_id == Repository.id)
            .where(Repository.user_id == user_id, Finding.status == "OPEN")
            .group_by(RiskAssessment.risk_level, RiskAssessment.priority)
        ).all()

        for r_level, r_priority, cnt in results:
            if r_level in levels:
                levels[r_level] += cnt
            if r_priority in priorities:
                priorities[r_priority] += cnt

        return {
            "risk_levels": levels,
            "priorities": priorities,
        }

    @staticmethod
    def get_risk_summary_for_repository(db: Session, repository_id: uuid.UUID | str, user_id: uuid.UUID | str) -> Dict[str, Any]:
        """
        Returns real risk level and priority counts for a specific repository.
        """
        if isinstance(repository_id, str):
            repository_id = uuid.UUID(repository_id)
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        levels = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        priorities = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}

        results = db.execute(
            select(RiskAssessment.risk_level, RiskAssessment.priority, func.count(Finding.id))
            .join(Finding, RiskAssessment.finding_id == Finding.id)
            .join(Repository, Finding.repository_id == Repository.id)
            .where(Repository.user_id == user_id, Finding.repository_id == repository_id, Finding.status == "OPEN")
            .group_by(RiskAssessment.risk_level, RiskAssessment.priority)
        ).all()

        for r_level, r_priority, cnt in results:
            if r_level in levels:
                levels[r_level] += cnt
            if r_priority in priorities:
                priorities[r_priority] += cnt

        return {
            "risk_levels": levels,
            "priorities": priorities,
        }
