"""
Unit tests for OSV dependency vulnerability scanner adapter.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.scanners.dependencies.osv import OSVScanner, determine_osv_severity


def test_determine_osv_severity_cvss():
    vuln_cvss = {
        "severity": [
            {"type": "CVSS_V3", "score": "8.5"}
        ]
    }
    assert determine_osv_severity(vuln_cvss) == "HIGH"

    vuln_critical = {
        "severity": [
            {"type": "CVSS_V3", "score": "9.8"}
        ]
    }
    assert determine_osv_severity(vuln_critical) == "CRITICAL"


def test_determine_osv_severity_database_specific():
    vuln_db = {
        "database_specific": {
            "severity": "MODERATE"
        }
    }
    assert determine_osv_severity(vuln_db) == "MEDIUM"

    vuln_crit = {
        "database_specific": {
            "severity": "CRITICAL"
        }
    }
    assert determine_osv_severity(vuln_crit) == "CRITICAL"


def test_osv_scanner_skipped_when_no_manifests(tmp_path):
    scanner = OSVScanner()
    res = scanner.scan(str(tmp_path))
    assert res.status == "SKIPPED"
    assert res.executed is True
    assert len(res.findings) == 0


def test_osv_scanner_parses_vulnerabilities(tmp_path):
    # Create fake requirements.txt
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.19.1\nflask==2.2.2\n")

    fake_osv_response = {
        "results": [
            {
                "vulns": [
                    {
                        "id": "GHSA-3833-g454-7pqd",
                        "aliases": ["CVE-2018-18074"],
                        "summary": "Redirect header leak vulnerability in requests",
                        "severity": [{"type": "CVSS_V3", "score": "7.5"}],
                        "affected": [
                            {
                                "ranges": [
                                    {"events": [{"fixed": "2.20.0"}]}
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "vulns": []
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fake_osv_response

    with patch("httpx.post", return_value=mock_resp):
        scanner = OSVScanner()
        res = scanner.scan(str(tmp_path))

    assert res.status == "COMPLETED"
    assert res.executed is True
    assert len(res.findings) == 1

    f = res.findings[0]
    assert f.type == "DEPENDENCY"
    assert f.package_name == "requests"
    assert f.installed_version == "2.19.1"
    assert f.fixed_version == "2.20.0"
    assert f.vulnerability_id == "CVE-2018-18074"
    assert "CVE-2018-18074" in f.aliases
    assert f.severity == "HIGH"
    assert "2.20.0" in f.recommendation
