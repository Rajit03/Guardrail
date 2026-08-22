import uuid
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.finding import Finding
from app.models.repository import Repository
from app.models.risk_assessment import RiskAssessment
from app.risk.engine import RiskEngine

logger = logging.getLogger(__name__)


class RiskService:
    @staticmethod
    def compute_and_save_risk_assessment(
        db: Session, finding: Finding, repository: Optional[Repository] = None
    ) -> RiskAssessment:
        """
        Calculates and persists/upserts a RiskAssessment for a finding.
        """
        if not repository:
            repository = db.scalar(select(Repository).where(Repository.id == finding.repository_id))

        exposure = repository.exposure if repository and hasattr(repository, "exposure") else "UNKNOWN"
        asset_criticality = (
            repository.asset_criticality if repository and hasattr(repository, "asset_criticality") else "UNKNOWN"
        )

        res = RiskEngine.evaluate(
            type=finding.type,
            severity=finding.severity,
            title=finding.title,
            description=finding.description,
            file_path=finding.file_path,
            scanner=finding.scanner,
            rule_id=finding.rule_id,
            recommendation=finding.recommendation,
            exposure=exposure,
            asset_criticality=asset_criticality,
        )

        # Check for existing assessment
        assessment = db.scalar(
            select(RiskAssessment).where(RiskAssessment.finding_id == finding.id)
        )

        if not assessment:
            assessment = RiskAssessment(
                finding_id=finding.id,
                risk_score=res.risk_score,
                risk_level=res.risk_level,
                priority=res.priority,
                severity_factor=res.severity_factor,
                exploitability_factor=res.exploitability_factor,
                exposure_factor=res.exposure_factor,
                asset_criticality_factor=res.asset_criticality_factor,
                confidence_factor=res.confidence_factor,
                explanation=res.explanation,
                recommended_action=res.recommended_action,
            )
            db.add(assessment)
        else:
            assessment.risk_score = res.risk_score
            assessment.risk_level = res.risk_level
            assessment.priority = res.priority
            assessment.severity_factor = res.severity_factor
            assessment.exploitability_factor = res.exploitability_factor
            assessment.exposure_factor = res.exposure_factor
            assessment.asset_criticality_factor = res.asset_criticality_factor
            assessment.confidence_factor = res.confidence_factor
            assessment.explanation = res.explanation
            assessment.recommended_action = res.recommended_action

        db.commit()
        db.refresh(assessment)
        return assessment

    @staticmethod
    def get_risk_assessment_for_finding(
        db: Session, finding_id: uuid.UUID | str, user_id: uuid.UUID | str
    ) -> Optional[RiskAssessment]:
        """
        Gets risk assessment for a finding with user ownership enforcement.
        """
        if isinstance(finding_id, str):
            finding_id = uuid.UUID(finding_id)
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        assessment = db.scalar(
            select(RiskAssessment)
            .join(Finding, RiskAssessment.finding_id == Finding.id)
            .join(Repository, Finding.repository_id == Repository.id)
            .where(Finding.id == finding_id, Repository.user_id == user_id)
        )
        return assessment

    @staticmethod
    def recalculate_finding_risk(
        db: Session, finding_id: uuid.UUID | str, user_id: uuid.UUID | str
    ) -> Optional[RiskAssessment]:
        """
        Recalculates risk assessment for a specific finding.
        """
        if isinstance(finding_id, str):
            finding_id = uuid.UUID(finding_id)
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        finding = db.scalar(
            select(Finding)
            .join(Repository, Finding.repository_id == Repository.id)
            .where(Finding.id == finding_id, Repository.user_id == user_id)
        )
        if not finding:
            return None

        repository = db.scalar(select(Repository).where(Repository.id == finding.repository_id))
        return RiskService.compute_and_save_risk_assessment(db, finding, repository)

    @staticmethod
    def recalculate_repository_risks(
        db: Session, repository_id: uuid.UUID | str, user_id: uuid.UUID | str
    ) -> Optional[Dict[str, Any]]:
        """
        Recalculates risk assessments for all findings in a repository.
        """
        if isinstance(repository_id, str):
            repository_id = uuid.UUID(repository_id)
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        repository = db.scalar(
            select(Repository).where(Repository.id == repository_id, Repository.user_id == user_id)
        )
        if not repository:
            return None

        findings = list(
            db.scalars(select(Finding).where(Finding.repository_id == repository_id)).all()
        )

        count = 0
        for f in findings:
            RiskService.compute_and_save_risk_assessment(db, f, repository)
            count += 1

        return {
            "repository_id": repository_id,
            "findings_processed": count,
            "assessments_created": count,
        }
