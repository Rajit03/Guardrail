import re
import uuid
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, case, func

from app.core.config import settings
from app.models.finding import Finding
from app.models.repository import Repository
from app.models.risk_assessment import RiskAssessment
from app.models.scan import Scan
from app.risk.scoring import calculate_security_score, determine_security_rating
from app.copilot.schemas import RelatedFindingItem
from app.copilot.security import sanitize_finding_for_ai, sanitize_untrusted_content


class SecurityContextBuilder:
    """
    Builds minimal, relevant, sanitized security context from Guardrail's database
    for the AI Copilot, enforcing tenant isolation and risk engine authority.
    """

    @staticmethod
    def classify_intent(query: str, finding_id: Optional[str] = None) -> str:
        q_lower = query.lower()
        if finding_id or any(kw in q_lower for kw in ["this finding", "explain finding", "why is this", "how to fix this", "remediate this"]):
            return "EXPLAIN_FINDING"
        if any(kw in q_lower for kw in ["fix first", "what first", "highest priority", "most critical", "top priority", "top risk", "start with"]):
            return "FIX_FIRST"
        if any(kw in q_lower for kw in ["secret", "credential", "api key", "password", "token", "leak", "gitleaks"]):
            return "SECRETS"
        if any(kw in q_lower for kw in ["dependenc", "package", "library", "cve", "ghsa", "vulnerab", "osv"]):
            return "DEPENDENCIES"
        if any(kw in q_lower for kw in ["changed", "previous scan", "last scan", "history", "trend", "since last", "comparison"]):
            return "SCAN_COMPARISON"
        if any(kw in q_lower for kw in ["how secure", "security score", "rating", "summary", "posture", "overview", "status"]):
            return "SECURITY_SUMMARY"
        return "GENERAL"

    @classmethod
    def build_context(
        cls,
        db: Session,
        user_id: uuid.UUID | str,
        query: str,
        repository_id: Optional[str] = None,
        finding_id: Optional[str] = None,
        scan_id: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], List[RelatedFindingItem], str]:
        """
        Retrieves relevant, sanitized context data and related finding references.
        Returns (context_dict, related_findings, intent).
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        intent = cls.classify_intent(query, finding_id)

        # 1. Resolve Repositories for the user (Tenant check)
        repo_query = select(Repository).where(Repository.user_id == user_id)
        if repository_id:
            try:
                r_uuid = uuid.UUID(repository_id)
                repo_query = repo_query.where(Repository.id == r_uuid)
            except ValueError:
                return {"error": "Invalid repository ID"}, [], intent

        repos = list(db.scalars(repo_query).all())
        if not repos:
            if repository_id or finding_id:
                # Specific repo or finding requested but not found or not owned
                raise ValueError("Resource not found or access denied")
            return {
                "user_summary": {
                    "total_repositories": 0,
                    "message": "User has no registered repositories in Guardrail."
                }
            }, [], intent

        repo_ids = [r.id for r in repos]
        repo_map = {r.id: r for r in repos}

        # 2. Specific Finding Context (EXPLAIN_FINDING)
        if finding_id:
            try:
                f_uuid = uuid.UUID(finding_id)
                finding_record = db.scalar(
                    select(Finding)
                    .where(Finding.id == f_uuid, Finding.repository_id.in_(repo_ids))
                )
                if not finding_record:
                    raise ValueError("Finding not found or access denied")

                assessment = db.scalar(
                    select(RiskAssessment).where(RiskAssessment.finding_id == finding_record.id)
                )

                f_dict = cls._finding_to_dict(finding_record, assessment)
                sanitized_f = sanitize_finding_for_ai(f_dict)
                
                repo = repo_map.get(finding_record.repository_id)
                context = {
                    "context_type": "SINGLE_FINDING_EXPLANATION",
                    "repository": {
                        "name": repo.name if repo else "Unknown",
                        "default_branch": repo.default_branch if repo else "main",
                    },
                    "target_finding": sanitized_f,
                }
                
                related = [cls._to_related_item(sanitized_f)]
                return context, related, intent

            except (ValueError, TypeError) as e:
                if str(e) == "Finding not found or access denied":
                    raise e
                raise ValueError("Invalid finding ID")

        # 3. Build Intent-Specific or General Context
        context_data: Dict[str, Any] = {
            "platform": "Guardrail Security Platform",
            "context_type": intent,
        }

        # Repository Overview & Score calculation
        repo_summaries = []
        all_open_assessments: List[Tuple[str, int]] = []

        for r in repos:
            open_ass = db.execute(
                select(Finding.severity, RiskAssessment.risk_score)
                .join(RiskAssessment, Finding.id == RiskAssessment.finding_id)
                .where(Finding.repository_id == r.id, Finding.status == "OPEN")
            ).all()
            all_open_assessments.extend([(row[0], row[1]) for row in open_ass])
            
            r_score = calculate_security_score([(row[0], row[1]) for row in open_ass])
            r_rating = determine_security_rating(r_score)
            
            repo_summaries.append({
                "id": str(r.id),
                "name": r.name,
                "security_score": r_score,
                "rating": r_rating["rating"],
                "risk_level": r_rating["risk_level"],
                "open_findings_count": len(open_ass),
            })

        overall_score = calculate_security_score(all_open_assessments)
        overall_rating = determine_security_rating(overall_score)

        context_data["overall_security"] = {
            "security_score": overall_score,
            "rating": overall_rating["rating"],
            "risk_level": overall_rating["risk_level"],
            "total_open_findings": len(all_open_assessments),
            "repositories": repo_summaries[:5],
        }

        # 4. Fetch targeted findings based on intent
        priority_order = case(
            (RiskAssessment.priority == "P0", 0),
            (RiskAssessment.priority == "P1", 1),
            (RiskAssessment.priority == "P2", 2),
            (RiskAssessment.priority == "P3", 3),
            else_=4,
        )

        findings_query = (
            select(Finding, RiskAssessment)
            .join(RiskAssessment, Finding.id == RiskAssessment.finding_id)
            .where(Finding.repository_id.in_(repo_ids), Finding.status == "OPEN")
        )

        if intent == "SECRETS":
            findings_query = findings_query.where(Finding.type == "SECRET")
        elif intent == "DEPENDENCIES":
            findings_query = findings_query.where(Finding.type == "DEPENDENCY")

        findings_query = findings_query.order_by(
            priority_order, desc(RiskAssessment.risk_score), desc(Finding.created_at)
        ).limit(settings.MAX_CONTEXT_FINDINGS)

        raw_findings = db.execute(findings_query).all()

        sanitized_findings = []
        related_items = []
        for f, a in raw_findings:
            f_dict = cls._finding_to_dict(f, a)
            safe_f = sanitize_finding_for_ai(f_dict)
            sanitized_findings.append(safe_f)
            related_items.append(cls._to_related_item(safe_f))

        context_data["active_findings"] = sanitized_findings

        # 5. Add Scan Comparison if requested or available
        if intent in ("SCAN_COMPARISON", "SECURITY_SUMMARY"):
            completed_scans = list(db.scalars(
                select(Scan)
                .where(Scan.repository_id.in_(repo_ids), Scan.status == "COMPLETED")
                .order_by(desc(Scan.created_at))
                .limit(2)
            ).all())

            if len(completed_scans) >= 2:
                latest_scan = completed_scans[0]
                prev_scan = completed_scans[1]

                prev_ass = db.execute(
                    select(Finding.severity, RiskAssessment.risk_score)
                    .join(RiskAssessment, Finding.id == RiskAssessment.finding_id)
                    .where(Finding.scan_id == prev_scan.id)
                ).all()
                prev_score = calculate_security_score([(row[0], row[1]) for row in prev_ass])
                score_delta = overall_score - prev_score

                context_data["scan_comparison"] = {
                    "has_previous_scan": True,
                    "latest_scan_date": latest_scan.created_at.isoformat() if latest_scan.created_at else None,
                    "previous_scan_date": prev_scan.created_at.isoformat() if prev_scan.created_at else None,
                    "score_change": score_delta,
                    "previous_score": prev_score,
                    "current_score": overall_score,
                }
            elif len(completed_scans) == 1:
                context_data["scan_comparison"] = {
                    "has_previous_scan": False,
                    "message": "This is the first scan, so there is no previous scan to compare.",
                    "latest_scan_date": completed_scans[0].created_at.isoformat() if completed_scans[0].created_at else None,
                }
            else:
                context_data["scan_comparison"] = {
                    "has_previous_scan": False,
                    "message": "No completed scans found for this repository yet.",
                }

        return context_data, related_items, intent

    @staticmethod
    def _finding_to_dict(finding: Finding, assessment: Optional[RiskAssessment]) -> Dict[str, Any]:
        return {
            "id": str(finding.id),
            "type": finding.type,
            "severity": finding.severity,
            "risk_score": assessment.risk_score if assessment else 0,
            "risk_level": assessment.risk_level if assessment else "INFO",
            "priority": assessment.priority if assessment else "P3",
            "title": finding.title,
            "description": finding.description,
            "file_path": finding.file_path,
            "line_number": finding.line_number,
            "scanner": finding.scanner,
            "rule_id": finding.rule_id,
            "status": finding.status,
            "recommendation": finding.recommendation,
            "package_name": finding.package_name,
            "installed_version": finding.installed_version,
            "fixed_version": finding.fixed_version,
            "vulnerability_id": finding.vulnerability_id,
        }

    @staticmethod
    def _to_related_item(f_data: Dict[str, Any]) -> RelatedFindingItem:
        return RelatedFindingItem(
            id=f_data.get("id", ""),
            title=f_data.get("title", ""),
            severity=f_data.get("severity", "MEDIUM"),
            risk_score=f_data.get("risk_score", 0),
            priority=f_data.get("priority", "P3"),
            type=f_data.get("type", "UNKNOWN"),
            file_path=f_data.get("file_path"),
            package_name=f_data.get("package_name"),
            vulnerability_id=f_data.get("vulnerability_id"),
        )
