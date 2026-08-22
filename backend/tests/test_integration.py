"""
Integration test for full Phase 3 scanning engine end-to-end flow:
Repository -> Scan -> Gitleaks & OSV Scanners -> Findings -> DB -> API
"""
import os
import json
import pytest
from unittest.mock import patch, MagicMock
from contextlib import contextmanager


def register_and_login(client, email="e2e@example.com", password="Password123!"):
    client.post("/api/auth/register", json={
        "name": "E2E User", "email": email, "password": password
    })
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


def test_end_to_end_security_scan_flow(client):
    token = register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Repository
    repo_res = client.post("/api/repositories", json={
        "name": "e2e-vulnerable-repo",
        "url": "https://github.com/example/e2e-vulnerable-repo",
        "provider": "github",
        "default_branch": "main"
    }, headers=headers)
    assert repo_res.status_code == 201
    repo_id = repo_res.json()["id"]

    # 2. Prepare fixture paths
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    node_dir = os.path.join(fixtures_dir, "dependencies", "node")

    @contextmanager
    def mock_acquire_repo(repo):
        yield node_dir

    # Mock Gitleaks execution returning a secret leak
    mock_gitleaks_report = [
        {
            "RuleID": "aws-access-token",
            "Secret": "AKIAIOSFODNN7EXAMPLE",
            "Description": "AWS Access Key",
            "File": "config.py",
            "StartLine": 12,
        }
    ]

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump(mock_gitleaks_report, f)
        report_path = f.name

    mock_git_res = MagicMock()
    mock_git_res.returncode = 1

    def fake_subprocess_run(cmd, **kwargs):
        if "version" in cmd:
            m = MagicMock()
            m.returncode = 0
            return m
        for i, arg in enumerate(cmd):
            if arg == "--report-path" and i + 1 < len(cmd):
                import shutil
                shutil.copy(report_path, cmd[i + 1])
        return mock_git_res

    # Mock OSV API returning a vulnerability for lodash
    mock_osv_res = MagicMock()
    mock_osv_res.status_code = 200
    mock_osv_res.json.return_value = {
        "results": [
            {
                "vulns": [
                    {
                        "id": "GHSA-p6mc-m468-83gw",
                        "summary": "Prototype Pollution in lodash",
                        "severity": [{"type": "CVSS_V3", "score": "7.5"}]
                    }
                ]
            }
        ]
    }

    # 3. Trigger Scan via API
    with patch("app.services.scan_service.acquire_repository", side_effect=mock_acquire_repo), \
         patch("subprocess.run", side_effect=fake_subprocess_run), \
         patch("httpx.post", return_value=mock_osv_res):

        scan_res = client.post(f"/api/repositories/{repo_id}/scan", headers=headers)

    os.unlink(report_path)

    assert scan_res.status_code == 200
    scan_data = scan_res.json()
    assert scan_data["status"] == "COMPLETED"
    assert scan_data["total_findings"] >= 2

    scan_id = scan_data["id"]

    # 4. Verify Scan Details API
    get_scan_res = client.get(f"/api/scans/{scan_id}", headers=headers)
    assert get_scan_res.status_code == 200
    assert get_scan_res.json()["total_findings"] == scan_data["total_findings"]

    # 5. Verify Scan Findings List API
    findings_res = client.get(f"/api/scans/{scan_id}/findings", headers=headers)
    assert findings_res.status_code == 200
    findings = findings_res.json()["findings"]
    assert len(findings) >= 2

    # Verify secret finding normalization & masking
    secret_findings = [f for f in findings if f["type"] == "SECRET"]
    assert len(secret_findings) == 1
    s_finding = secret_findings[0]
    assert s_finding["scanner"] == "gitleaks"
    assert s_finding["severity"] == "HIGH"
    assert s_finding["rule_id"] == "aws-access-token"
    # Verify raw secret is NOT present verbatim
    assert "AKIAIOSFODNN7EXAMPLE" not in (s_finding.get("evidence") or "")
    assert "****" in (s_finding.get("evidence") or "")

    # Verify dependency finding normalization
    dep_findings = [f for f in findings if f["type"] == "DEPENDENCY"]
    assert len(dep_findings) >= 1
    d_finding = dep_findings[0]
    assert d_finding["scanner"] == "osv"
    assert d_finding["severity"] == "HIGH"
    assert "GHSA-p6mc-m468-83gw" in d_finding["rule_id"]

    # 6. Verify Finding Details API
    f_detail_res = client.get(f"/api/findings/{s_finding['id']}", headers=headers)
    assert f_detail_res.status_code == 200
    assert f_detail_res.json()["id"] == s_finding["id"]

    # 7. Verify Dashboard Metrics API via repository list / finding list
    all_findings_res = client.get("/api/findings", headers=headers)
    assert all_findings_res.status_code == 200
    assert len(all_findings_res.json()["findings"]) >= 2
