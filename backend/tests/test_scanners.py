"""
Tests for scanner implementations.
OSV calls are mocked to avoid live network dependency.
No real credentials are used anywhere in this file.
"""
import os
import json
import pytest
from unittest.mock import patch, MagicMock
from app.scanners.secrets.gitleaks import GitleaksScanner
from app.scanners.dependencies.osv import OSVScanner

# ─── Fixture paths ────────────────────────────────────────────────
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
VULNERABLE_DIR = os.path.join(FIXTURES_DIR, "secrets", "vulnerable")
CLEAN_DIR = os.path.join(FIXTURES_DIR, "secrets", "clean")
NODE_DEP_DIR = os.path.join(FIXTURES_DIR, "dependencies", "node")
PYTHON_DEP_DIR = os.path.join(FIXTURES_DIR, "dependencies", "python")


# ─── Secret Scanner Tests ──────────────────────────────────────────

class TestGitleaksScanner:
    def test_gitleaks_not_installed_returns_failed_status(self, tmp_path):
        """If gitleaks is not installed, return ScannerResult with status FAILED."""
        scanner = GitleaksScanner()
        with patch("subprocess.run", side_effect=FileNotFoundError("gitleaks not found")):
            res = scanner.scan(str(tmp_path))
        assert res.executed is False
        assert res.status == "FAILED"
        assert len(res.findings) == 0

    def test_gitleaks_crash_returns_failed_status(self, tmp_path):
        """If gitleaks crashes with unexpected exit code, return ScannerResult with status FAILED."""
        scanner = GitleaksScanner()
        mock_result = MagicMock()
        mock_result.returncode = 2  # Unexpected error, not 0 (clean) or 1 (leak)
        mock_result.stderr = "fatal error"
        with patch("subprocess.run", return_value=mock_result):
            res = scanner.scan(str(tmp_path))
        assert res.status == "FAILED"
        assert len(res.findings) == 0

    def test_gitleaks_clean_returns_completed_status(self, tmp_path):
        """A clean directory with no secrets returns zero findings."""
        scanner = GitleaksScanner()
        (tmp_path / "readme.txt").write_text("This is a clean file with no secrets.")

        mock_version = MagicMock(returncode=0, stdout="v8.18.2")
        mock_result = MagicMock(returncode=0)

        def mock_run(cmd, **kwargs):
            if "version" in cmd:
                return mock_version
            return mock_result

        with patch("subprocess.run", side_effect=mock_run), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=0):
            res = scanner.scan(str(tmp_path))

        assert res.status == "COMPLETED_NO_FINDINGS"
        assert len(res.findings) == 0

    def test_gitleaks_detects_secret_and_masks_value(self, tmp_path):
        """
        If gitleaks reports a finding, the evidence must be masked.
        Secret value must NOT appear verbatim in returned evidence.
        """
        scanner = GitleaksScanner()
        fake_secret = "aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpP"
        gitleaks_report = [
            {
                "RuleID": "generic-api-key",
                "Secret": fake_secret,
                "Description": "Generic API Key",
                "File": ".env",
                "StartLine": 1,
            }
        ]

        mock_version = MagicMock(returncode=0, stdout="v8.18.2")
        mock_result = MagicMock(returncode=1)

        def fake_run(cmd, **kwargs):
            if "version" in cmd:
                return mock_version
            for i, arg in enumerate(cmd):
                if arg == "--report-path" and i + 1 < len(cmd):
                    with open(cmd[i + 1], "w", encoding="utf-8") as f:
                        json.dump(gitleaks_report, f)
            return mock_result

        with patch("subprocess.run", side_effect=fake_run):
            res = scanner.scan(str(tmp_path))

        assert res.status == "COMPLETED_WITH_FINDINGS"
        assert len(res.findings) == 1
        finding = res.findings[0]
        assert finding.type == "SECRET"
        assert finding.scanner == "gitleaks"
        assert finding.rule_id == "generic-api-key"
        assert fake_secret not in (finding.evidence or "")
        assert "****" in (finding.evidence or "")


# ─── Dependency Scanner Tests ──────────────────────────────────────

class TestOSVScanner:
    def test_recognizes_package_json(self):
        """OSV scanner should detect package.json files."""
        scanner = OSVScanner()
        mock_osv_response = MagicMock()
        mock_osv_response.status_code = 200
        mock_osv_response.json.return_value = {"results": [{"vulns": []}]}

        with patch("httpx.post", return_value=mock_osv_response):
            res = scanner.scan(NODE_DEP_DIR)
        assert res.status == "COMPLETED"
        assert isinstance(res.findings, list)

    def test_recognizes_requirements_txt(self):
        """OSV scanner should detect requirements.txt files."""
        scanner = OSVScanner()
        mock_osv_response = MagicMock()
        mock_osv_response.status_code = 200
        mock_osv_response.json.return_value = {"results": [{"vulns": []}, {"vulns": []}]}

        with patch("httpx.post", return_value=mock_osv_response):
            res = scanner.scan(PYTHON_DEP_DIR)
        assert res.status == "COMPLETED"
        assert isinstance(res.findings, list)

    def test_vuln_response_normalized(self):
        """When OSV returns a vuln, it should be converted to a FindingData."""
        scanner = OSVScanner()
        mock_osv_response = MagicMock()
        mock_osv_response.status_code = 200
        mock_osv_response.json.return_value = {
            "results": [
                {"vulns": [{"id": "GHSA-xxxx-yyyy-zzzz", "summary": "Prototype Pollution"}]},
                {"vulns": []},
            ]
        }

        with patch("httpx.post", return_value=mock_osv_response):
            res = scanner.scan(NODE_DEP_DIR)

        assert res.status == "COMPLETED"
        assert len(res.findings) >= 1
        f = res.findings[0]
        assert f.type == "DEPENDENCY"
        assert f.scanner == "osv"
        assert "GHSA-xxxx-yyyy-zzzz" in f.rule_id

    def test_osv_failure_handled_gracefully(self, tmp_path):
        """If OSV API is unavailable, return FAILED status and don't crash."""
        scanner = OSVScanner()
        (tmp_path / "requirements.txt").write_text("requests==2.20.0\n")

        with patch("httpx.post", side_effect=Exception("OSV unavailable")):
            res = scanner.scan(str(tmp_path))
        assert res.status == "FAILED"
        assert len(res.findings) == 0

    def test_malformed_dependency_file_handled(self, tmp_path):
        """Malformed package.json should not crash the scanner."""
        scanner = OSVScanner()
        (tmp_path / "package.json").write_text("this is not valid json {{{")

        mock_osv_response = MagicMock()
        mock_osv_response.status_code = 200
        mock_osv_response.json.return_value = {"results": []}

        with patch("httpx.post", return_value=mock_osv_response):
            res = scanner.scan(str(tmp_path))
        assert res.status == "SKIPPED"
        assert len(res.findings) == 0

    def test_empty_directory_returns_skipped(self, tmp_path):
        """A directory with no manifest files returns SKIPPED status without querying OSV."""
        scanner = OSVScanner()
        with patch("httpx.post") as mock_post:
            res = scanner.scan(str(tmp_path))
        mock_post.assert_not_called()
        assert res.status == "SKIPPED"
        assert len(res.findings) == 0
