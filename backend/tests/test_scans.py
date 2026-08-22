"""
API integration tests for Scan and Finding endpoints.
Uses the in-memory database from conftest.py.
All scanner calls are mocked to avoid live network/gitleaks dependency.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.scanners.base import FindingData, ScannerResult


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
        title="lodash vulnerability — GHSA-xxxx-yyyy-zzzz",
        scanner="osv",
        description="Prototype Pollution",
        file_path="package.json",
        rule_id="GHSA-xxxx-yyyy-zzzz",
        recommendation="Upgrade lodash.",
        package_name="lodash",
        installed_version="4.17.20",
        fixed_version="4.17.21",
        vulnerability_id="GHSA-xxxx-yyyy-zzzz",
        aliases=["GHSA-xxxx-yyyy-zzzz"]
    )
]

MOCK_RESULTS = {
    "gitleaks": ScannerResult(scanner_name="gitleaks", executed=True, status="COMPLETED", raw_findings_count=1, normalized_findings_count=1, findings=[MOCK_FINDINGS[0]]),
    "osv": ScannerResult(scanner_name="osv", executed=True, status="COMPLETED", raw_findings_count=1, normalized_findings_count=1, findings=[MOCK_FINDINGS[1]])
}


def scan_with_findings(client, token, repo_id):
    """Helper: run a mocked scan on a given repo and return the scan response."""
    from contextlib import contextmanager

    @contextmanager
    def mock_acquire(repo):
        yield "/tmp/fakerepo"

    with patch("app.services.scan_service.acquire_repository", side_effect=mock_acquire), \
         patch("app.scanners.runner.ScannerRunner.run_all", return_value=(MOCK_FINDINGS, MOCK_RESULTS)):
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
        token = register_and_login(client, "scanner@example.com")
        repo_id = create_repo(client, token)

        scan_data = scan_with_findings(client, token, repo_id)

        assert scan_data["status"] == "COMPLETED"
        assert scan_data["repository_id"] == repo_id
        assert scan_data["total_findings"] == 2
        assert scan_data["scan_summary"] is not None

    def test_cannot_scan_other_users_repository(self, client):
        """User A cannot trigger a scan on User B's repository."""
        token_a = register_and_login(client, "usera@example.com")
        token_b = register_and_login(client, "userb@example.com")

        repo_b_id = create_repo(client, token_b, "https://github.com/octocat/Spoon-Knife")

        r = client.post(f"/api/repositories/{repo_b_id}/scan", headers=auth_headers(token_a))
        assert r.status_code == 404

    def test_scan_with_invalid_repository_id(self, client):
        """Scanning a non-existent UUID returns 404."""
        token = register_and_login(client, "badid@example.com")
        r = client.post(
            "/api/repositories/00000000-0000-0000-0000-000000000099/scan",
            headers=auth_headers(token)
        )
        assert r.status_code == 404


# ── Scan Retrieval Tests ───────────────────────────────────────────

class TestScanRetrieval:
    def test_get_scan_by_id(self, client):
        """Authenticated user can retrieve details of their completed scan."""
        token = register_and_login(client, "getscan@example.com")
        repo_id = create_repo(client, token)
        scan_data = scan_with_findings(client, token, repo_id)
        scan_id = scan_data["id"]

        r = client.get(f"/api/scans/{scan_id}", headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json()["id"] == scan_id
        assert r.json()["status"] == "COMPLETED"
        assert r.json()["total_findings"] == 2

    def test_cannot_get_other_users_scan(self, client):
        """User A cannot view User B's scan details."""
        token_a = register_and_login(client, "scana@example.com")
        token_b = register_and_login(client, "scanb@example.com")

        repo_b_id = create_repo(client, token_b, "https://github.com/octocat/Spoon-Knife")
        scan_data = scan_with_findings(client, token_b, repo_b_id)
        scan_b_id = scan_data["id"]

        r = client.get(f"/api/scans/{scan_b_id}", headers=auth_headers(token_a))
        assert r.status_code == 404


# ── Findings API Tests ─────────────────────────────────────────────

class TestFindingsAPI:
    def test_findings_list_for_user(self, client):
        """Listing findings returns findings belonging to user's repositories."""
        token = register_and_login(client, "listfind@example.com")
        repo_id = create_repo(client, token)
        scan_with_findings(client, token, repo_id)

        r = client.get("/api/findings", headers=auth_headers(token))
        assert r.status_code == 200
        findings = r.json()["findings"]
        assert len(findings) == 2

    def test_finding_details(self, client):
        """Can fetch a single finding by ID."""
        token = register_and_login(client, "detailfind@example.com")
        repo_id = create_repo(client, token)
        scan_with_findings(client, token, repo_id)

        findings_resp = client.get("/api/findings", headers=auth_headers(token))
        finding_id = findings_resp.json()["findings"][0]["id"]

        r = client.get(f"/api/findings/{finding_id}", headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json()["id"] == finding_id

    def test_other_user_cannot_get_finding_detail(self, client):
        """User A cannot access User B's finding detail."""
        token_a = register_and_login(client, "finda@example.com")
        token_b = register_and_login(client, "findb@example.com")

        repo_b_id = create_repo(client, token_b, "https://github.com/octocat/Spoon-Knife")
        scan_with_findings(client, token_b, repo_b_id)

        findings_b = client.get("/api/findings", headers=auth_headers(token_b)).json()["findings"]
        finding_b_id = findings_b[0]["id"]

        r = client.get(f"/api/findings/{finding_b_id}", headers=auth_headers(token_a))
        assert r.status_code == 404

    def test_scan_findings_endpoint(self, client):
        """GET /api/scans/{scan_id}/findings returns findings for that scan."""
        token = register_and_login(client, "scanfind@example.com")
        repo_id = create_repo(client, token)
        scan_data = scan_with_findings(client, token, repo_id)
        scan_id = scan_data["id"]

        r = client.get(f"/api/scans/{scan_id}/findings", headers=auth_headers(token))
        assert r.status_code == 200
        assert len(r.json()["findings"]) == 2

    def test_secret_evidence_is_masked(self, client):
        """Evidence string must not expose raw secrets in full."""
        token = register_and_login(client, "masked@example.com")
        repo_id = create_repo(client, token)
        scan_with_findings(client, token, repo_id)

        r = client.get("/api/findings", headers=auth_headers(token))
        findings = r.json()["findings"]
        secret_finding = next(f for f in findings if f["type"] == "SECRET")
        assert "aAbB****" in secret_finding["evidence"]

    def test_filter_by_severity(self, client):
        """Filtering by severity returns matching findings."""
        token = register_and_login(client, "sevfilter@example.com")
        repo_id = create_repo(client, token)
        scan_with_findings(client, token, repo_id)

        r = client.get("/api/findings?severity=HIGH", headers=auth_headers(token))
        assert r.status_code == 200
        assert len(r.json()["findings"]) == 2

        r_low = client.get("/api/findings?severity=LOW", headers=auth_headers(token))
        assert r_low.status_code == 200
        assert len(r_low.json()["findings"]) == 0

    def test_filter_by_type(self, client):
        """Filtering by type returns matching findings."""
        token = register_and_login(client, "typefilter@example.com")
        repo_id = create_repo(client, token)
        scan_with_findings(client, token, repo_id)

        r = client.get("/api/findings?type=SECRET", headers=auth_headers(token))
        assert r.status_code == 200
        findings = r.json()["findings"]
        assert len(findings) == 1
        assert findings[0]["type"] == "SECRET"
