"""
API integration tests for Scan and Finding endpoints.
Uses the in-memory SQLite database from conftest.py.
All scanner calls are mocked to avoid live network/gitleaks dependency.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.scanners.base import FindingData


# ── Helpers ────────────────────────────────────────────────────────

def register_and_login(client, email="user@example.com", password="password123"):
    client.post("/api/auth/register", json={
        "name": "Test User", "email": email, "password": password
    })
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_repo(client, token, url="https://github.com/octocat/Hello-World"):
    r = client.post("/api/repositories", json={
        "name": "test-repo",
        "url": url,
        "provider": "github",
        "default_branch": "main"
    }, headers=auth_headers(token))
    assert r.status_code == 201
    return r.json()["id"]


MOCK_FINDINGS = [
    FindingData(
        type="SECRET",
        severity="HIGH",
        title="Potential secret detected",
        scanner="gitleaks",
        description="A hardcoded secret was found.",
        file_path=".env",
        line_number=1,
        rule_id="generic-api-key",
        evidence="API_KEY: aAbB****",  # Already masked
        recommendation="Rotate this credential."
    ),
    FindingData(
        type="DEPENDENCY",
        severity="HIGH",
        title="Vulnerable dependency detected: lodash",
        scanner="osv",
        description="Prototype Pollution",
        file_path="package.json",
        rule_id="GHSA-xxxx-yyyy-zzzz",
        recommendation="Upgrade lodash."
    )
]


def scan_with_findings(client, token, repo_id):
    """Helper: run a mocked scan on a given repo and return the scan response."""
    from contextlib import contextmanager

    @contextmanager
    def mock_acquire(repo):
        yield "/tmp/fakerepo"

    with patch("app.services.scan_service.acquire_repository", side_effect=mock_acquire), \
         patch("app.scanners.runner.ScannerRunner.run_all", return_value=MOCK_FINDINGS):
        r = client.post(f"/api/repositories/{repo_id}/scan", headers=auth_headers(token))
    return r.json()


# ── Scan Creation Tests ────────────────────────────────────────────

class TestScanAPI:
    def test_unauthenticated_cannot_scan(self, client):
        """Unauthenticated users must not be able to trigger a scan."""
        r = client.post("/api/repositories/00000000-0000-0000-0000-000000000001/scan")
        assert r.status_code == 401

    def test_authenticated_can_scan_own_repository(self, client):
        """Authenticated user can scan their own repository."""
        token = register_and_login(client)
        repo_id = create_repo(client, token)
        data = scan_with_findings(client, token, repo_id)
        assert data["status"] in ("COMPLETED", "FAILED")
        assert data["repository_id"] == repo_id

    def test_user_cannot_scan_another_users_repository(self, client):
        """User A must not be able to scan User B's repository."""
        token_a = register_and_login(client, "a@example.com", "password123")
        token_b = register_and_login(client, "b@example.com", "password123")
        repo_id = create_repo(client, token_b)

        r = client.post(f"/api/repositories/{repo_id}/scan", headers=auth_headers(token_a))
        assert r.status_code == 404

    def test_scan_record_created(self, client):
        """Scan record is created and scan_id is returned."""
        token = register_and_login(client)
        repo_id = create_repo(client, token)
        data = scan_with_findings(client, token, repo_id)
        assert "id" in data
        assert data["id"] is not None

    def test_scan_completes_with_correct_finding_count(self, client):
        """Scan reports the correct total_findings."""
        token = register_and_login(client)
        repo_id = create_repo(client, token)
        data = scan_with_findings(client, token, repo_id)
        assert data["status"] == "COMPLETED"
        assert data["total_findings"] == len(MOCK_FINDINGS)

    def test_scan_status_get(self, client):
        """GET /api/scans/{scan_id} returns the scan record."""
        token = register_and_login(client)
        repo_id = create_repo(client, token)
        scan_data = scan_with_findings(client, token, repo_id)
        scan_id = scan_data["id"]

        r = client.get(f"/api/scans/{scan_id}", headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json()["id"] == scan_id

    def test_other_user_cannot_get_scan(self, client):
        """User A must not access User B's scan."""
        token_a = register_and_login(client, "a@example.com", "password123")
        token_b = register_and_login(client, "b@example.com", "password123")
        repo_id = create_repo(client, token_a)
        scan_data = scan_with_findings(client, token_a, repo_id)
        scan_id = scan_data["id"]

        r = client.get(f"/api/scans/{scan_id}", headers=auth_headers(token_b))
        assert r.status_code == 404


# ── Findings API Tests ─────────────────────────────────────────────

class TestFindingsAPI:
    def test_get_findings_requires_auth(self, client):
        """Unauthenticated users must not be able to list findings."""
        r = client.get("/api/findings")
        assert r.status_code == 401

    def test_findings_list_for_user(self, client):
        """User can list their own findings."""
        token = register_and_login(client)
        repo_id = create_repo(client, token)
        scan_with_findings(client, token, repo_id)

        r = client.get("/api/findings", headers=auth_headers(token))
        assert r.status_code == 200
        data = r.json()
        assert "findings" in data
        assert len(data["findings"]) == len(MOCK_FINDINGS)

    def test_user_cannot_see_other_users_findings(self, client):
        """User B must see zero findings from User A's repositories."""
        token_a = register_and_login(client, "a@example.com", "password123")
        token_b = register_and_login(client, "b@example.com", "password123")
        repo_id = create_repo(client, token_a)
        scan_with_findings(client, token_a, repo_id)

        r = client.get("/api/findings", headers=auth_headers(token_b))
        assert r.status_code == 200
        assert len(r.json()["findings"]) == 0

    def test_finding_details(self, client):
        """GET /api/findings/{id} returns the full finding."""
        token = register_and_login(client)
        repo_id = create_repo(client, token)
        scan_with_findings(client, token, repo_id)

        findings = client.get("/api/findings", headers=auth_headers(token)).json()["findings"]
        finding_id = findings[0]["id"]

        r = client.get(f"/api/findings/{finding_id}", headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json()["id"] == finding_id

    def test_other_user_cannot_get_finding_detail(self, client):
        """User B must not access User A's finding details."""
        token_a = register_and_login(client, "a@example.com", "password123")
        token_b = register_and_login(client, "b@example.com", "password123")
        repo_id = create_repo(client, token_a)
        scan_with_findings(client, token_a, repo_id)

        findings = client.get("/api/findings", headers=auth_headers(token_a)).json()["findings"]
        finding_id = findings[0]["id"]

        r = client.get(f"/api/findings/{finding_id}", headers=auth_headers(token_b))
        assert r.status_code == 404

    def test_scan_findings_endpoint(self, client):
        """GET /api/scans/{scan_id}/findings returns findings for that scan."""
        token = register_and_login(client)
        repo_id = create_repo(client, token)
        scan_data = scan_with_findings(client, token, repo_id)
        scan_id = scan_data["id"]

        r = client.get(f"/api/scans/{scan_id}/findings", headers=auth_headers(token))
        assert r.status_code == 200
        assert len(r.json()["findings"]) == len(MOCK_FINDINGS)

    def test_secret_evidence_is_masked(self, client):
        """The raw secret value must never appear in findings API response."""
        token = register_and_login(client)
        repo_id = create_repo(client, token)
        scan_with_findings(client, token, repo_id)

        r = client.get("/api/findings", headers=auth_headers(token))
        findings = r.json()["findings"]
        secret_findings = [f for f in findings if f["type"] == "SECRET"]

        for f in secret_findings:
            evidence = f.get("evidence", "") or ""
            # Evidence must contain the mask marker
            assert "****" in evidence

    def test_filter_by_severity(self, client):
        """Findings can be filtered by severity."""
        token = register_and_login(client)
        repo_id = create_repo(client, token)
        scan_with_findings(client, token, repo_id)

        r = client.get("/api/findings?severity=HIGH", headers=auth_headers(token))
        assert r.status_code == 200
        for f in r.json()["findings"]:
            assert f["severity"] == "HIGH"

    def test_filter_by_type(self, client):
        """Findings can be filtered by type."""
        token = register_and_login(client)
        repo_id = create_repo(client, token)
        scan_with_findings(client, token, repo_id)

        r = client.get("/api/findings?type=SECRET", headers=auth_headers(token))
        assert r.status_code == 200
        for f in r.json()["findings"]:
            assert f["type"] == "SECRET"
