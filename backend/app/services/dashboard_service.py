import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case, desc, asc, or_

from app.models.finding import Finding
from app.models.repository import Repository
from app.models.risk_assessment import RiskAssessment
from app.models.scan import Scan
from app.risk.scoring import calculate_security_score, determine_security_rating
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    DashboardSummaryFindingCounts,
    DashboardSummaryTypeCounts,
    DashboardSummaryRepositories,
    DashboardScannerStatus,
    DashboardPriorityFinding,
    DashboardRecentFinding,
    DashboardRecentScan,
    DashboardRiskTrendPoint,
    DashboardImprovements,
    DashboardRepositoryItem,
    FindingSeverityCounts,
    DashboardRepositoriesResponse,
    DashboardFindingsPaginatedResponse,
    DashboardRiskTrendResponse,
)


def detect_primary_language(file_list: Optional[List[str]]) -> str:
    """
    Detects the primary programming language from repository scan inventory.
    """
    if not file_list:
        return "Unknown"

    ext_counts: Dict[str, int] = {}
    ext_to_lang = {
        ".py": "Python",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".mjs": "JavaScript",
        ".cjs": "JavaScript",
        ".r": "R",
        ".rmd": "R",
        ".go": "Go",
        ".java": "Java",
        ".jar": "Java",
        ".rs": "Rust",
        ".cpp": "C++",
        ".cc": "C++",
        ".c": "C",
        ".h": "C/C++",
        ".hpp": "C++",
        ".rb": "Ruby",
        ".php": "PHP",
        ".cs": "C#",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
    }

    for file_path in file_list:
        p_lower = file_path.lower()
        for ext, lang in ext_to_lang.items():
            if p_lower.endswith(ext):
                ext_counts[lang] = ext_counts.get(lang, 0) + 1

    if not ext_counts:
        # Check manifest heuristics
        file_set = {f.lower() for f in file_list}
        if any("requirements.txt" in f or "pyproject.toml" in f for f in file_set):
            return "Python"
        if any("package.json" in f for f in file_set):
            return "JavaScript"
        if any("description" in f or "namespace" in f for f in file_set):
            return "R"
        if any("cargo.toml" in f for f in file_set):
            return "Rust"
        if any("go.mod" in f for f in file_set):
            return "Go"
        return "General"

    # Return language with most occurrences
    primary = max(ext_counts.items(), key=lambda x: x[1])[0]
    return primary


class DashboardService:
    @staticmethod
    def get_dashboard_summary(db: Session, user_id: uuid.UUID | str) -> DashboardSummaryResponse:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        # 1. User repositories summary
        repos = list(db.scalars(
            select(Repository).where(Repository.user_id == user_id)
        ).all())
        repo_ids = [r.id for r in repos]
        repo_name_map = {r.id: r.name for r in repos}

        if not repo_ids:
            # Clean empty state for users without repositories
            return DashboardSummaryResponse(
                security_score=100,
                risk_level="LOW",
                rating="Excellent",
                score_change=None,
                findings=DashboardSummaryFindingCounts(),
                types=DashboardSummaryTypeCounts(),
                repositories=DashboardSummaryRepositories(total=0, scanned=0, unscanned=0),
                scanners={
                    "gitleaks": DashboardScannerStatus(name="Gitleaks", status="Operational", operational=True, version="8.18.2"),
                    "osv": DashboardScannerStatus(name="OSV", status="Operational", operational=True),
                },
                priority_findings=[],
                recent_findings=[],
                recent_scans=[],
                risk_trend=[],
                improvements=DashboardImprovements(),
            )

        scanned_repos_count = sum(1 for r in repos if r.last_scan_at is not None)
        unscanned_repos_count = len(repos) - scanned_repos_count

        # 2. Findings Aggregations (Counts by status, severity, type)
        finding_rows = db.execute(
            select(Finding.severity, Finding.status, Finding.type, func.count(Finding.id))
            .where(Finding.repository_id.in_(repo_ids))
            .group_by(Finding.severity, Finding.status, Finding.type)
        ).all()

        crit_count = 0
        high_count = 0
        med_count = 0
        low_count = 0
        info_count = 0
        open_count = 0
        resolved_count = 0
        secret_count = 0
        dep_count = 0

        for sev, stat, f_type, cnt in finding_rows:
            if stat == "OPEN":
                open_count += cnt
                if sev == "CRITICAL":
                    crit_count += cnt
                elif sev == "HIGH":
                    high_count += cnt
                elif sev == "MEDIUM":
                    med_count += cnt
                elif sev == "LOW":
                    low_count += cnt
                elif sev == "INFO":
                    info_count += cnt

                if f_type == "SECRET":
                    secret_count += cnt
                elif f_type == "DEPENDENCY":
                    dep_count += cnt
            elif stat == "RESOLVED":
                resolved_count += cnt

        total_findings_count = open_count + resolved_count

        # 3. Overall Security Score calculation from active open findings
        open_assessments = db.execute(
            select(Finding.severity, RiskAssessment.risk_score)
            .join(RiskAssessment, Finding.id == RiskAssessment.finding_id)
            .where(Finding.repository_id.in_(repo_ids), Finding.status == "OPEN")
        ).all()

        assessment_tuples = [(row[0], row[1]) for row in open_assessments]
        current_score = calculate_security_score(assessment_tuples)
        rating_data = determine_security_rating(current_score)

        # 4. Top Priority Findings (Top 5 P0/P1/P2/P3 open findings)
        priority_order = case(
            (RiskAssessment.priority == "P0", 0),
            (RiskAssessment.priority == "P1", 1),
            (RiskAssessment.priority == "P2", 2),
            (RiskAssessment.priority == "P3", 3),
            else_=4,
        )
        priority_query = (
            select(Finding, RiskAssessment)
            .join(RiskAssessment, Finding.id == RiskAssessment.finding_id)
            .where(Finding.repository_id.in_(repo_ids), Finding.status == "OPEN")
            .order_by(priority_order, desc(RiskAssessment.risk_score), desc(Finding.created_at))
            .limit(5)
        )
        priority_results = db.execute(priority_query).all()
        priority_findings_list: List[DashboardPriorityFinding] = []
        for finding, assessment in priority_results:
            priority_findings_list.append(
                DashboardPriorityFinding(
                    id=finding.id,
                    repository_id=finding.repository_id,
                    repository_name=repo_name_map.get(finding.repository_id, "Unknown"),
                    scan_id=finding.scan_id,
                    type=finding.type,
                    severity=finding.severity,
                    title=finding.title,
                    description=finding.description,
                    file_path=finding.file_path,
                    line_number=finding.line_number,
                    scanner=finding.scanner,
                    rule_id=finding.rule_id,
                    evidence=finding.evidence,
                    recommendation=finding.recommendation,
                    status=finding.status,
                    package_name=finding.package_name,
                    vulnerability_id=finding.vulnerability_id,
                    risk_score=assessment.risk_score if assessment else 0,
                    risk_level=assessment.risk_level if assessment else "INFO",
                    priority=assessment.priority if assessment else "P3",
                    created_at=finding.created_at,
                )
            )

        # 5. Recent Findings (Latest 10 findings)
        recent_query = (
            select(Finding, RiskAssessment)
            .outerjoin(RiskAssessment, Finding.id == RiskAssessment.finding_id)
            .where(Finding.repository_id.in_(repo_ids))
            .order_by(desc(Finding.created_at))
            .limit(10)
        )
        recent_results = db.execute(recent_query).all()
        recent_findings_list: List[DashboardRecentFinding] = []
        for finding, assessment in recent_results:
            recent_findings_list.append(
                DashboardRecentFinding(
                    id=finding.id,
                    repository_id=finding.repository_id,
                    repository_name=repo_name_map.get(finding.repository_id, "Unknown"),
                    scan_id=finding.scan_id,
                    type=finding.type,
                    severity=finding.severity,
                    title=finding.title,
                    description=finding.description,
                    file_path=finding.file_path,
                    line_number=finding.line_number,
                    scanner=finding.scanner,
                    rule_id=finding.rule_id,
                    status=finding.status,
                    package_name=finding.package_name,
                    vulnerability_id=finding.vulnerability_id,
                    risk_score=assessment.risk_score if assessment else 0,
                    risk_level=assessment.risk_level if assessment else "INFO",
                    priority=assessment.priority if assessment else "P3",
                    created_at=finding.created_at,
                )
            )

        # 6. Recent Scans (Latest 10 scans across repositories)
        recent_scans_query = (
            select(Scan)
            .where(Scan.repository_id.in_(repo_ids))
            .order_by(desc(Scan.created_at))
            .limit(10)
        )
        scans_list = list(db.scalars(recent_scans_query).all())
        recent_scans_list: List[DashboardRecentScan] = []

        gitleaks_operational = True
        gitleaks_status_label = "Operational"
        osv_operational = True
        osv_status_label = "Operational"
        latest_scan_time = None

        for scan in scans_list:
            if not latest_scan_time:
                latest_scan_time = scan.created_at

            duration = None
            if scan.started_at and scan.completed_at:
                duration = max(0, int((scan.completed_at - scan.started_at).total_seconds()))

            scan_summary = scan.scan_summary or {}
            scanners_info = scan_summary.get("scanners", {})

            # Check scanner health from latest scan
            if scan == scans_list[0] and scanners_info:
                gl = scanners_info.get("gitleaks", {})
                if gl.get("status") == "FAILED":
                    gitleaks_operational = False
                    gitleaks_status_label = "Failed"

                osv = scanners_info.get("osv", {})
                if osv.get("status") == "FAILED":
                    osv_operational = False
                    osv_status_label = "Failed"

            recent_scans_list.append(
                DashboardRecentScan(
                    id=scan.id,
                    repository_id=scan.repository_id,
                    repository_name=repo_name_map.get(scan.repository_id, "Unknown"),
                    status=scan.status,
                    started_at=scan.started_at,
                    completed_at=scan.completed_at,
                    duration_seconds=duration,
                    total_findings=scan.total_findings,
                    scanners=scanners_info,
                    created_at=scan.created_at,
                )
            )

        # 7. Risk Trend (Timeline across historical scans)
        all_completed_scans = list(db.scalars(
            select(Scan)
            .where(Scan.repository_id.in_(repo_ids), Scan.status == "COMPLETED")
            .order_by(asc(Scan.created_at))
        ).all())

        risk_trend_points: List[DashboardRiskTrendPoint] = []
        for s in all_completed_scans:
            # Query findings associated with this scan to compute historical score
            s_assessments = db.execute(
                select(Finding.severity, RiskAssessment.risk_score)
                .join(RiskAssessment, Finding.id == RiskAssessment.finding_id)
                .where(Finding.scan_id == s.id)
            ).all()
            s_score = calculate_security_score([(row[0], row[1]) for row in s_assessments])

            risk_trend_points.append(
                DashboardRiskTrendPoint(
                    scan_id=s.id,
                    timestamp=s.created_at,
                    date=s.created_at.strftime("%b %d, %H:%M") if s.created_at else "N/A",
                    security_score=s_score,
                    finding_count=s.total_findings,
                    repository_id=s.repository_id,
                    repository_name=repo_name_map.get(s.repository_id, "Unknown"),
                )
            )

        # 8. Security Improvement & Scan Comparison
        # Compare latest scan with previous scan if at least 2 completed scans exist
        score_change = None
        previous_score = None
        new_findings_count = 0
        resolved_findings_count = 0
        persistent_findings_count = 0

        if len(all_completed_scans) >= 2:
            latest_scan = all_completed_scans[-1]
            prev_scan = all_completed_scans[-2]

            prev_assessments = db.execute(
                select(Finding.severity, RiskAssessment.risk_score)
                .join(RiskAssessment, Finding.id == RiskAssessment.finding_id)
                .where(Finding.scan_id == prev_scan.id)
            ).all()
            previous_score = calculate_security_score([(r[0], r[1]) for r in prev_assessments])
            score_change = current_score - previous_score

            # Findings for the latest scan
            latest_scan_findings = list(db.scalars(
                select(Finding).where(Finding.scan_id == latest_scan.id, Finding.status == "OPEN")
            ).all())

            scan_threshold = latest_scan.started_at or latest_scan.created_at

            new_findings_count = sum(1 for f in latest_scan_findings if f.created_at >= scan_threshold)
            persistent_findings_count = sum(1 for f in latest_scan_findings if f.created_at < scan_threshold)

            # Resolved findings in the latest scan window
            resolved_findings_count = db.scalar(
                select(func.count(Finding.id)).where(
                    Finding.repository_id.in_(repo_ids),
                    Finding.status == "RESOLVED",
                    Finding.updated_at >= scan_threshold,
                )
            ) or 0
        elif len(all_completed_scans) == 1:
            new_findings_count = all_completed_scans[0].total_findings
            persistent_findings_count = new_findings_count

        return DashboardSummaryResponse(
            security_score=current_score,
            risk_level=rating_data["risk_level"],
            rating=rating_data["rating"],
            score_change=score_change,
            findings=DashboardSummaryFindingCounts(
                total=total_findings_count,
                critical=crit_count,
                high=high_count,
                medium=med_count,
                low=low_count,
                info=info_count,
                open=open_count,
                resolved=resolved_count,
            ),
            types=DashboardSummaryTypeCounts(
                secret=secret_count,
                dependency=dep_count,
            ),
            repositories=DashboardSummaryRepositories(
                total=len(repos),
                scanned=scanned_repos_count,
                unscanned=unscanned_repos_count,
            ),
            scanners={
                "gitleaks": DashboardScannerStatus(
                    name="Gitleaks",
                    status=gitleaks_status_label,
                    operational=gitleaks_operational,
                    version="8.18.2",
                    last_run_at=latest_scan_time,
                ),
                "osv": DashboardScannerStatus(
                    name="OSV",
                    status=osv_status_label,
                    operational=osv_operational,
                    last_run_at=latest_scan_time,
                ),
            },
            priority_findings=priority_findings_list,
            recent_findings=recent_findings_list,
            recent_scans=recent_scans_list,
            risk_trend=risk_trend_points,
            improvements=DashboardImprovements(
                new_findings=new_findings_count,
                resolved_findings=resolved_findings_count,
                persistent_findings=persistent_findings_count,
                score_change=score_change,
                previous_score=previous_score,
            ),
        )

    @staticmethod
    def get_dashboard_repositories(db: Session, user_id: uuid.UUID | str) -> DashboardRepositoriesResponse:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        repos = list(db.scalars(
            select(Repository).where(Repository.user_id == user_id).order_by(desc(Repository.created_at))
        ).all())

        items: List[DashboardRepositoryItem] = []
        for repo in repos:
            # Query severity counts for open findings
            severity_rows = db.execute(
                select(Finding.severity, Finding.status, func.count(Finding.id))
                .where(Finding.repository_id == repo.id)
                .group_by(Finding.severity, Finding.status)
            ).all()

            crit = 0
            high = 0
            med = 0
            low = 0
            info = 0
            open_cnt = 0
            res_cnt = 0

            for sev, stat, cnt in severity_rows:
                if stat == "OPEN":
                    open_cnt += cnt
                    if sev == "CRITICAL":
                        crit += cnt
                    elif sev == "HIGH":
                        high += cnt
                    elif sev == "MEDIUM":
                        med += cnt
                    elif sev == "LOW":
                        low += cnt
                    elif sev == "INFO":
                        info += cnt
                elif stat == "RESOLVED":
                    res_cnt += cnt

            # Compute repository-specific security score
            repo_assessments = db.execute(
                select(Finding.severity, RiskAssessment.risk_score)
                .join(RiskAssessment, Finding.id == RiskAssessment.finding_id)
                .where(Finding.repository_id == repo.id, Finding.status == "OPEN")
            ).all()
            repo_score = calculate_security_score([(r[0], r[1]) for r in repo_assessments])
            rating_data = determine_security_rating(repo_score)

            # Latest scan & language detection
            latest_scan = db.scalar(
                select(Scan)
                .where(Scan.repository_id == repo.id)
                .order_by(desc(Scan.created_at))
                .limit(1)
            )
            scans_count = db.scalar(
                select(func.count(Scan.id)).where(Scan.repository_id == repo.id)
            ) or 0

            file_list = None
            if latest_scan and latest_scan.scan_summary:
                file_list = latest_scan.scan_summary.get("file_list")
            primary_lang = detect_primary_language(file_list)

            items.append(
                DashboardRepositoryItem(
                    id=repo.id,
                    name=repo.name,
                    url=repo.url,
                    provider=repo.provider,
                    default_branch=repo.default_branch,
                    primary_language=primary_lang,
                    security_score=repo_score,
                    risk_level=rating_data["risk_level"],
                    rating=rating_data["rating"],
                    finding_counts=FindingSeverityCounts(
                        critical=crit,
                        high=high,
                        medium=med,
                        low=low,
                        info=info,
                        total_open=open_cnt,
                        total_resolved=res_cnt,
                    ),
                    last_scan_at=latest_scan.completed_at or latest_scan.started_at if latest_scan else None,
                    last_scan_status=latest_scan.status if latest_scan else None,
                    scans_count=scans_count,
                )
            )

        return DashboardRepositoriesResponse(
            repositories=items,
            total=len(items),
        )

    @staticmethod
    def get_dashboard_findings(
        db: Session,
        user_id: uuid.UUID | str,
        repository_id: Optional[str] = None,
        severity: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None,
        scanner: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
    ) -> DashboardFindingsPaginatedResponse:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        # Base query joining user's repositories and risk assessments
        base_query = (
            select(Finding, RiskAssessment, Repository.name.label("repo_name"))
            .join(Repository, Finding.repository_id == Repository.id)
            .outerjoin(RiskAssessment, Finding.id == RiskAssessment.finding_id)
            .where(Repository.user_id == user_id)
        )

        if repository_id:
            try:
                repo_uuid = uuid.UUID(repository_id)
                base_query = base_query.where(Finding.repository_id == repo_uuid)
            except ValueError:
                return DashboardFindingsPaginatedResponse(findings=[], total=0, page=page, page_size=page_size, total_pages=0)

        if severity:
            base_query = base_query.where(Finding.severity == severity.upper())
        if type:
            base_query = base_query.where(Finding.type == type.upper())
        if status:
            base_query = base_query.where(Finding.status == status.upper())
        if scanner:
            base_query = base_query.where(Finding.scanner == scanner.lower())

        if search:
            search_pattern = f"%{search.strip()}%"
            base_query = base_query.where(
                or_(
                    Finding.title.ilike(search_pattern),
                    Finding.package_name.ilike(search_pattern),
                    Finding.vulnerability_id.ilike(search_pattern),
                    Finding.file_path.ilike(search_pattern),
                    Repository.name.ilike(search_pattern),
                    Finding.rule_id.ilike(search_pattern),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_count = db.scalar(count_query) or 0

        # Sorting
        if sort_by == "risk_score":
            base_query = base_query.order_by(desc(RiskAssessment.risk_score), desc(Finding.created_at))
        elif sort_by == "priority":
            priority_order = case(
                (RiskAssessment.priority == "P0", 0),
                (RiskAssessment.priority == "P1", 1),
                (RiskAssessment.priority == "P2", 2),
                (RiskAssessment.priority == "P3", 3),
                else_=4,
            )
            base_query = base_query.order_by(priority_order, desc(RiskAssessment.risk_score), desc(Finding.created_at))
        elif sort_by == "severity":
            sev_order = case(
                (Finding.severity == "CRITICAL", 0),
                (Finding.severity == "HIGH", 1),
                (Finding.severity == "MEDIUM", 2),
                (Finding.severity == "LOW", 3),
                else_=4,
            )
            base_query = base_query.order_by(sev_order, desc(RiskAssessment.risk_score), desc(Finding.created_at))
        elif sort_by == "created_at":
            base_query = base_query.order_by(desc(Finding.created_at))
        else:
            # Default priority then risk score
            priority_order = case(
                (RiskAssessment.priority == "P0", 0),
                (RiskAssessment.priority == "P1", 1),
                (RiskAssessment.priority == "P2", 2),
                (RiskAssessment.priority == "P3", 3),
                else_=4,
            )
            base_query = base_query.order_by(priority_order, desc(RiskAssessment.risk_score), desc(Finding.created_at))

        # Pagination
        offset = max(0, (page - 1) * page_size)
        paginated_query = base_query.offset(offset).limit(page_size)
        rows = db.execute(paginated_query).all()

        findings_list: List[DashboardRecentFinding] = []
        for finding, assessment, repo_name in rows:
            findings_list.append(
                DashboardRecentFinding(
                    id=finding.id,
                    repository_id=finding.repository_id,
                    repository_name=repo_name or "Unknown",
                    scan_id=finding.scan_id,
                    type=finding.type,
                    severity=finding.severity,
                    title=finding.title,
                    description=finding.description,
                    file_path=finding.file_path,
                    line_number=finding.line_number,
                    scanner=finding.scanner,
                    rule_id=finding.rule_id,
                    status=finding.status,
                    package_name=finding.package_name,
                    vulnerability_id=finding.vulnerability_id,
                    risk_score=assessment.risk_score if assessment else 0,
                    risk_level=assessment.risk_level if assessment else "INFO",
                    priority=assessment.priority if assessment else "P3",
                    created_at=finding.created_at,
                )
            )

        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1

        return DashboardFindingsPaginatedResponse(
            findings=findings_list,
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def get_risk_trend(db: Session, user_id: uuid.UUID | str) -> DashboardRiskTrendResponse:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        repos = list(db.scalars(
            select(Repository).where(Repository.user_id == user_id)
        ).all())
        repo_ids = [r.id for r in repos]
        repo_name_map = {r.id: r.name for r in repos}

        if not repo_ids:
            return DashboardRiskTrendResponse(points=[], total_scans=0)

        scans = list(db.scalars(
            select(Scan)
            .where(Scan.repository_id.in_(repo_ids), Scan.status == "COMPLETED")
            .order_by(asc(Scan.created_at))
        ).all())

        points: List[DashboardRiskTrendPoint] = []
        for s in scans:
            s_assessments = db.execute(
                select(Finding.severity, RiskAssessment.risk_score)
                .join(RiskAssessment, Finding.id == RiskAssessment.finding_id)
                .where(Finding.scan_id == s.id)
            ).all()
            s_score = calculate_security_score([(row[0], row[1]) for row in s_assessments])

            points.append(
                DashboardRiskTrendPoint(
                    scan_id=s.id,
                    timestamp=s.created_at,
                    date=s.created_at.strftime("%b %d, %H:%M") if s.created_at else "N/A",
                    security_score=s_score,
                    finding_count=s.total_findings,
                    repository_id=s.repository_id,
                    repository_name=repo_name_map.get(s.repository_id, "Unknown"),
                )
            )

        return DashboardRiskTrendResponse(
            points=points,
            total_scans=len(points),
        )
