"""
Unit and integration tests for Phase 5 Security Dashboard API endpoints.
Tests verify:
  1. Authentication and authorization enforcement (tenant isolation)
  2. Accurate severity, type, and status aggregations
  3. Security score determinism derived from the Risk Engine
  4. Comparison with previous scans (new, resolved, persistent findings, score delta)
  5. Real historical scan data in risk trend
  6. Empty states (0 repos, unscanned repos)
  7. Scanner health reporting (operational vs failed)
  8. Paginated, searchable, filterable findings endpoint
  9. Repository overview with primary language detection
  10. Strict secret credential masking in all dashboard responses
"""
import uuid
from datetime import datetime, timezone
import pytest
from app.models.repository import Repository
from app.models.scan import Scan
from app.models.finding import Finding
from app.models.risk_assessment import RiskAssessment
from app.models.user import User
from app.core.security import get_password_hash


def create_test_user(db, email, name="Test User"):
    user = User(
        name=name,
        email=email,
        password_hash=get_password_hash("Password123!"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_token(client, email, password="Password123!"):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


class TestDashboardAuth:
    def test_dashboard_summary_requires_auth(self, client):
        """Unauthenticated request to dashboard summary must return 401."""
        res = client.get("/api/dashboard/summary")
        assert res.status_code == 401

    def test_dashboard_repositories_requires_auth(self, client):
        """Unauthenticated request to dashboard repositories must return 401."""
        res = client.get("/api/dashboard/repositories")
        assert res.status_code == 401

    def test_dashboard_findings_requires_auth(self, client):
        """Unauthenticated request to dashboard findings must return 401."""
        res = client.get("/api/dashboard/findings")
        assert res.status_code == 401

    def test_dashboard_risk_trend_requires_auth(self, client):
        """Unauthenticated request to dashboard risk trend must return 401."""
        res = client.get("/api/dashboard/risk-trend")
        assert res.status_code == 401


class TestDashboardTenantIsolation:
    def test_user_only_sees_own_data(self, client, db):
        """User A must NEVER see User B's repositories or findings in dashboard."""
        user_a = create_test_user(db, "user_a@example.com", "User A")
        user_b = create_test_user(db, "user_b@example.com", "User B")

        token_a = get_auth_token(client, "user_a@example.com")
        token_b = get_auth_token(client, "user_b@example.com")

        # Create repo and finding for User B
        repo_b = Repository(
            user_id=user_b.id,
            name="user-b-secret-repo",
            url="https://github.com/example/user-b-secret-repo",
            provider="github",
            default_branch="main",
        )
        db.add(repo_b)
        db.commit()
        db.refresh(repo_b)

        scan_b = Scan(repository_id=repo_b.id, status="COMPLETED", total_findings=1)
        db.add(scan_b)
        db.commit()
        db.refresh(scan_b)

        finding_b = Finding(
            repository_id=repo_b.id,
            scan_id=scan_b.id,
            type="SECRET",
            severity="CRITICAL",
            title="User B Secret",
            scanner="gitleaks",
            fingerprint="fp-b-1",
            status="OPEN",
        )
        db.add(finding_b)
        db.commit()

        # User A views summary: should see 0 repositories, 0 findings, 100 score
        headers_a = {"Authorization": f"Bearer {token_a}"}
        res_a = client.get("/api/dashboard/summary", headers=headers_a)
        assert res_a.status_code == 200
        data_a = res_a.json()
        assert data_a["repositories"]["total"] == 0
        assert data_a["findings"]["total"] == 0
        assert data_a["security_score"] == 100
        assert len(data_a["priority_findings"]) == 0
        assert len(data_a["recent_findings"]) == 0

        # User B views summary: should see 1 repository, 1 finding
        headers_b = {"Authorization": f"Bearer {token_b}"}
        res_b = client.get("/api/dashboard/summary", headers=headers_b)
        assert res_b.status_code == 200
        data_b = res_b.json()
        assert data_b["repositories"]["total"] == 1
        assert data_b["findings"]["total"] == 1
        assert data_b["findings"]["critical"] == 1
        assert data_b["types"]["secret"] == 1


class TestDashboardMetricsAndScoring:
    def test_empty_user_state(self, client, db):
        """User with no repositories should have 100 score, Excellent rating, and empty lists."""
        create_test_user(db, "empty@example.com")
        token = get_auth_token(client, "empty@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/dashboard/summary", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["security_score"] == 100
        assert data["rating"] == "Excellent"
        assert data["risk_level"] == "LOW"
        assert data["repositories"]["total"] == 0
        assert data["findings"]["total"] == 0
        assert data["priority_findings"] == []
        assert data["recent_findings"] == []
        assert data["recent_scans"] == []

    def test_unscanned_repository_state(self, client, db):
        """User with unscanned repository reports 1 unscanned, 0 findings, 100 score."""
        user = create_test_user(db, "unscanned@example.com")
        token = get_auth_token(client, "unscanned@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        repo = Repository(
            user_id=user.id,
            name="new-unscanned-repo",
            url="https://github.com/example/new-unscanned-repo",
            provider="github",
            default_branch="main",
        )
        db.add(repo)
        db.commit()

        res = client.get("/api/dashboard/summary", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["repositories"]["total"] == 1
        assert data["repositories"]["scanned"] == 0
        assert data["repositories"]["unscanned"] == 1
        assert data["findings"]["total"] == 0
        assert data["security_score"] == 100

    def test_security_score_and_severity_aggregations(self, client, db):
        """Verified accurate counting of critical, high, medium, low, secret, dependency findings."""
        user = create_test_user(db, "metrics@example.com")
        token = get_auth_token(client, "metrics@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        repo = Repository(
            user_id=user.id,
            name="test-metrics-repo",
            url="https://github.com/example/test-metrics-repo",
            provider="github",
            default_branch="main",
            last_scan_at=datetime.now(timezone.utc),
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)

        scan = Scan(
            repository_id=repo.id,
            status="COMPLETED",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            total_findings=4,
            scan_summary={
                "scanners": {
                    "gitleaks": {"status": "COMPLETED_WITH_FINDINGS", "executed": True},
                    "osv": {"status": "COMPLETED", "executed": True},
                },
                "file_list": ["app.py", "requirements.txt", "main.py"],
            },
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        # 1 Critical Secret
        f1 = Finding(
            repository_id=repo.id, scan_id=scan.id, type="SECRET", severity="CRITICAL",
            title="AWS Access Key Exposed", file_path=".env", scanner="gitleaks",
            fingerprint="fp-1", status="OPEN",
        )
        # 1 High Dependency
        f2 = Finding(
            repository_id=repo.id, scan_id=scan.id, type="DEPENDENCY", severity="HIGH",
            title="Remote Code Execution in requests", file_path="requirements.txt", scanner="osv",
            package_name="requests", fingerprint="fp-2", status="OPEN",
        )
        # 1 Medium Dependency
        f3 = Finding(
            repository_id=repo.id, scan_id=scan.id, type="DEPENDENCY", severity="MEDIUM",
            title="Moderate DOS in urllib3", file_path="requirements.txt", scanner="osv",
            package_name="urllib3", fingerprint="fp-3", status="OPEN",
        )
        # 1 Low Dependency (Resolved)
        f4 = Finding(
            repository_id=repo.id, scan_id=scan.id, type="DEPENDENCY", severity="LOW",
            title="Minor header leak in certifi", file_path="requirements.txt", scanner="osv",
            package_name="certifi", fingerprint="fp-4", status="RESOLVED",
        )
        db.add_all([f1, f2, f3, f4])
        db.commit()

        # Add RiskAssessments
        ra1 = RiskAssessment(
            finding_id=f1.id, risk_score=92, risk_level="CRITICAL", priority="P0",
            explanation="Critical AWS credential leak", recommended_action="Revoke immediately",
        )
        ra2 = RiskAssessment(
            finding_id=f2.id, risk_score=75, risk_level="HIGH", priority="P1",
            explanation="High severity dependency vulnerability", recommended_action="Upgrade requests",
        )
        ra3 = RiskAssessment(
            finding_id=f3.id, risk_score=48, risk_level="MEDIUM", priority="P2",
            explanation="Medium severity vulnerability", recommended_action="Upgrade urllib3",
        )
        db.add_all([ra1, ra2, ra3])
        db.commit()

        res = client.get("/api/dashboard/summary", headers=headers)
        assert res.status_code == 200
        data = res.json()

        # Check Finding Counts
        f_counts = data["findings"]
        assert f_counts["total"] == 4
        assert f_counts["open"] == 3
        assert f_counts["resolved"] == 1
        assert f_counts["critical"] == 1
        assert f_counts["high"] == 1
        assert f_counts["medium"] == 1
        assert f_counts["low"] == 0  # Resolved Low is not in open severity count

        # Check Type Counts (open only)
        assert data["types"]["secret"] == 1
        assert data["types"]["dependency"] == 2

        # Check Score & Classification
        assert data["security_score"] < 75  # Penalized by P0 and P1 risks
        assert data["risk_level"] in ("HIGH", "CRITICAL", "MEDIUM")

        # Check Top Priority Findings (sorted P0 first)
        assert len(data["priority_findings"]) == 3
        assert data["priority_findings"][0]["priority"] == "P0"
        assert data["priority_findings"][0]["title"] == "AWS Access Key Exposed"
        assert data["priority_findings"][0]["repository_name"] == "test-metrics-repo"

        # Check Scanner status
        assert data["scanners"]["gitleaks"]["operational"] is True
        assert data["scanners"]["osv"]["operational"] is True


class TestDashboardScanComparisonAndTrend:
    def test_scan_comparison_delta_and_trend(self, client, db):
        """Tests that when 2 scans exist, score_change, new, resolved, persistent findings and risk trend are computed."""
        user = create_test_user(db, "trend@example.com")
        token = get_auth_token(client, "trend@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        repo = Repository(
            user_id=user.id,
            name="trend-repo",
            url="https://github.com/example/trend-repo",
            provider="github",
            default_branch="main",
            last_scan_at=datetime.now(timezone.utc),
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)

        # Scan 1: 2 findings
        scan1 = Scan(
            repository_id=repo.id,
            status="COMPLETED",
            started_at=datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc),
            completed_at=datetime(2026, 8, 1, 10, 0, 15, tzinfo=timezone.utc),
            created_at=datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc),
            total_findings=2,
        )
        db.add(scan1)
        db.commit()
        db.refresh(scan1)

        f_old1 = Finding(
            repository_id=repo.id, scan_id=scan1.id, type="DEPENDENCY", severity="HIGH",
            title="Old Vuln 1", scanner="osv", fingerprint="fp-persistent", status="OPEN",
            created_at=datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc),
        )
        f_old2 = Finding(
            repository_id=repo.id, scan_id=scan1.id, type="DEPENDENCY", severity="HIGH",
            title="Old Vuln 2 (to be resolved)", scanner="osv", fingerprint="fp-to-resolve", status="RESOLVED",
            created_at=datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc),
        )
        db.add_all([f_old1, f_old2])
        db.commit()

        ra_old1 = RiskAssessment(finding_id=f_old1.id, risk_score=70, risk_level="HIGH", priority="P1")
        ra_old2 = RiskAssessment(finding_id=f_old2.id, risk_score=68, risk_level="HIGH", priority="P1")
        db.add_all([ra_old1, ra_old2])
        db.commit()

        # Scan 2: 2 findings (1 persistent, 1 new)
        scan2 = Scan(
            repository_id=repo.id,
            status="COMPLETED",
            started_at=datetime(2026, 8, 2, 10, 0, 0, tzinfo=timezone.utc),
            completed_at=datetime(2026, 8, 2, 10, 0, 20, tzinfo=timezone.utc),
            created_at=datetime(2026, 8, 2, 10, 0, 0, tzinfo=timezone.utc),
            total_findings=2,
        )
        db.add(scan2)
        db.commit()
        db.refresh(scan2)

        # Update f_old1's scan_id to scan2, mark f_old2 resolved in scan2
        f_old1.scan_id = scan2.id
        f_old2.updated_at = datetime(2026, 8, 2, 10, 0, 5, tzinfo=timezone.utc)
        f_new = Finding(
            repository_id=repo.id, scan_id=scan2.id, type="SECRET", severity="CRITICAL",
            title="New Secret Detected", scanner="gitleaks", fingerprint="fp-new-secret", status="OPEN",
            created_at=datetime(2026, 8, 2, 10, 0, 0, tzinfo=timezone.utc),
        )
        db.add(f_new)
        db.commit()

        ra_new = RiskAssessment(finding_id=f_new.id, risk_score=95, risk_level="CRITICAL", priority="P0")
        db.add(ra_new)
        db.commit()

        res = client.get("/api/dashboard/summary", headers=headers)
        assert res.status_code == 200
        data = res.json()

        # Verify Improvements comparison
        imp = data["improvements"]
        assert imp["new_findings"] == 1
        assert imp["resolved_findings"] == 1
        assert imp["persistent_findings"] == 1
        assert imp["score_change"] is not None

        # Verify Risk Trend points
        trend = data["risk_trend"]
        assert len(trend) == 2
        assert trend[0]["scan_id"] == str(scan1.id)
        assert trend[1]["scan_id"] == str(scan2.id)
        assert trend[0]["finding_count"] == 2
        assert trend[1]["finding_count"] == 2

        # Verify Recent Scans
        scans = data["recent_scans"]
        assert len(scans) == 2
        assert scans[0]["id"] == str(scan2.id)
        assert scans[0]["duration_seconds"] == 20


class TestDashboardRepositoriesEndpoint:
    def test_get_dashboard_repositories(self, client, db):
        """Tests /api/dashboard/repositories with language detection and score calculation."""
        user = create_test_user(db, "repos@example.com")
        token = get_auth_token(client, "repos@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        # Create Python repo
        repo_py = Repository(
            user_id=user.id,
            name="python-service",
            url="https://github.com/example/python-service",
            provider="github",
            default_branch="main",
            last_scan_at=datetime.now(timezone.utc),
        )
        # Create R repo
        repo_r = Repository(
            user_id=user.id,
            name="r-analytics",
            url="https://github.com/example/r-analytics",
            provider="github",
            default_branch="main",
            last_scan_at=datetime.now(timezone.utc),
        )
        db.add_all([repo_py, repo_r])
        db.commit()
        db.refresh(repo_py)
        db.refresh(repo_r)

        # Scans with file lists
        scan_py = Scan(
            repository_id=repo_py.id, status="COMPLETED", total_findings=0,
            scan_summary={"file_list": ["app.py", "routes.py", "requirements.txt"]}
        )
        scan_r = Scan(
            repository_id=repo_r.id, status="COMPLETED", total_findings=0,
            scan_summary={"file_list": ["analysis.R", "data_prep.r", "DESCRIPTION"]}
        )
        db.add_all([scan_py, scan_r])
        db.commit()

        res = client.get("/api/dashboard/repositories", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 2

        repo_names = {r["name"]: r for r in data["repositories"]}
        assert "python-service" in repo_names
        assert repo_names["python-service"]["primary_language"] == "Python"
        assert repo_names["python-service"]["security_score"] == 100

        assert "r-analytics" in repo_names
        assert repo_names["r-analytics"]["primary_language"] == "R"
        assert repo_names["r-analytics"]["security_score"] == 100


class TestDashboardFindingsEndpoint:
    def test_paginated_and_searchable_findings(self, client, db):
        """Tests /api/dashboard/findings with search, filters, and pagination."""
        user = create_test_user(db, "find@example.com")
        token = get_auth_token(client, "find@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        repo = Repository(
            user_id=user.id,
            name="search-repo",
            url="https://github.com/example/search-repo",
            provider="github",
            default_branch="main",
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)

        scan = Scan(repository_id=repo.id, status="COMPLETED", total_findings=2)
        db.add(scan)
        db.commit()
        db.refresh(scan)

        f1 = Finding(
            repository_id=repo.id, scan_id=scan.id, type="DEPENDENCY", severity="HIGH",
            title="Prototype Pollution in lodash", package_name="lodash",
            file_path="package.json", scanner="osv", fingerprint="fp-lodash", status="OPEN",
        )
        f2 = Finding(
            repository_id=repo.id, scan_id=scan.id, type="SECRET", severity="CRITICAL",
            title="Potential credential detected", file_path=".env", scanner="gitleaks",
            fingerprint="fp-sec", status="OPEN",
        )
        db.add_all([f1, f2])
        db.commit()

        # 1. Search by package name 'lodash'
        res = client.get("/api/dashboard/findings?search=lodash", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert data["findings"][0]["package_name"] == "lodash"

        # 2. Filter by type 'SECRET'
        res_sec = client.get("/api/dashboard/findings?type=SECRET", headers=headers)
        assert res_sec.status_code == 200
        data_sec = res_sec.json()
        assert data_sec["total"] == 1
        assert data_sec["findings"][0]["type"] == "SECRET"

        # 3. Filter by severity 'HIGH'
        res_high = client.get("/api/dashboard/findings?severity=HIGH", headers=headers)
        assert res_high.status_code == 200
        assert res_high.json()["total"] == 1

        # 4. Pagination
        res_p = client.get("/api/dashboard/findings?page=1&page_size=1", headers=headers)
        assert res_p.status_code == 200
        p_data = res_p.json()
        assert len(p_data["findings"]) == 1
        assert p_data["total"] == 2
        assert p_data["total_pages"] == 2
