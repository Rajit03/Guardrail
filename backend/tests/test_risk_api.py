"""
API integration and authorization tests for Risk Engine endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
from contextlib import contextmanager
from app.scanners.base import FindingData


def register_and_login(client, email="risk_user@example.com", password="password123"):
    client.post("/api/auth/register", json={
        "name": "Risk Test User", "email": email, "password": password
    })
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_repo(client, token, url="https://github.com/octocat/Hello-World"):
    r = client.post("/api/repositories", json={
        "name": "risk-repo",
        "url": url,
        "provider": "github",
        "default_branch": "main"
    }, headers=auth_headers(token))
    return r.json()["id"]


MOCK_FINDINGS = [
    FindingData(
        type="SECRET",
        severity="CRITICAL",
        title="Hardcoded AWS Secret Key",
        scanner="gitleaks",
        description="A hardcoded secret was found.",
        file_path="config.py",
        line_number=10,
        rule_id="aws-secret-key",
        evidence="AWS_SECRET: aAbB****",
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
    @contextmanager
    def mock_acquire(repo):
        yield "/tmp/fakerepo"

    with patch("app.services.scan_service.acquire_repository", side_effect=mock_acquire), \
         patch("app.scanners.runner.ScannerRunner.run_all", return_value=MOCK_FINDINGS):
        r = client.post(f"/api/repositories/{repo_id}/scan", headers=auth_headers(token))
    return r.json()


def test_scan_creates_risk_assessments(client):
    token = register_and_login(client, "user1@example.com")
    repo_id = create_repo(client, token)
    scan_data = scan_with_findings(client, token, repo_id)
    assert scan_data["status"] == "COMPLETED"

    # Fetch findings for scan
    findings_res = client.get("/api/findings", headers=auth_headers(token))
    assert findings_res.status_code == 200
    findings = findings_res.json()["findings"]
    assert len(findings) == 2

    # Verify risk fields are attached
    f1 = findings[0]
    assert "risk_score" in f1
    assert "risk_level" in f1
    assert "priority" in f1
    assert f1["risk_assessment"] is not None


def test_get_finding_risk_endpoint(client):
    token = register_and_login(client, "user2@example.com")
    repo_id = create_repo(client, token)
    scan_with_findings(client, token, repo_id)

    findings = client.get("/api/findings", headers=auth_headers(token)).json()["findings"]
    finding_id = findings[0]["id"]

    risk_res = client.get(f"/api/findings/{finding_id}/risk", headers=auth_headers(token))
    assert risk_res.status_code == 200
    risk_data = risk_res.json()
    assert risk_data["finding_id"] == finding_id
    assert "risk_score" in risk_data
    assert "factors" in risk_data
    assert "explanation" in risk_data
    assert "recommended_action" in risk_data


def test_user_cannot_access_other_users_risk_assessment(client):
    token_a = register_and_login(client, "userA@example.com")
    token_b = register_and_login(client, "userB@example.com")

    repo_id = create_repo(client, token_a)
    scan_with_findings(client, token_a, repo_id)

    findings = client.get("/api/findings", headers=auth_headers(token_a)).json()["findings"]
    finding_id = findings[0]["id"]

    # User B tries to view User A's risk assessment
    r = client.get(f"/api/findings/{finding_id}/risk", headers=auth_headers(token_b))
    assert r.status_code == 404

    # User B tries to recalculate User A's risk assessment
    r_recalc = client.post(f"/api/findings/{finding_id}/risk/recalculate", headers=auth_headers(token_b))
    assert r_recalc.status_code == 404

    # User B tries to recalculate User A's repository risk assessments
    r_repo_recalc = client.post(f"/api/repositories/{repo_id}/risk/recalculate", headers=auth_headers(token_b))
    assert r_repo_recalc.status_code == 404


def test_recalculate_endpoints(client):
    token = register_and_login(client, "user_recalc@example.com")
    repo_id = create_repo(client, token)
    scan_with_findings(client, token, repo_id)

    findings = client.get("/api/findings", headers=auth_headers(token)).json()["findings"]
    finding_id = findings[0]["id"]

    # Recalculate single finding risk
    recalc_res = client.post(f"/api/findings/{finding_id}/risk/recalculate", headers=auth_headers(token))
    assert recalc_res.status_code == 200
    assert recalc_res.json()["finding_id"] == finding_id

    # Recalculate repository risks
    repo_recalc_res = client.post(f"/api/repositories/{repo_id}/risk/recalculate", headers=auth_headers(token))
    assert repo_recalc_res.status_code == 200
    assert repo_recalc_res.json()["findings_processed"] == 2


def test_findings_sorting_and_filtering_by_risk(client):
    token = register_and_login(client, "user_filters@example.com")
    repo_id = create_repo(client, token)
    scan_with_findings(client, token, repo_id)

    # Filter by priority
    p_res = client.get("/api/findings?priority=P0", headers=auth_headers(token))
    assert p_res.status_code == 200

    # Filter by risk_level
    r_res = client.get("/api/findings?risk_level=HIGH", headers=auth_headers(token))
    assert r_res.status_code == 200

    # Sort by priority
    sort_res = client.get("/api/findings?sort_by=priority", headers=auth_headers(token))
    assert sort_res.status_code == 200
    findings = sort_res.json()["findings"]
    assert len(findings) == 2
