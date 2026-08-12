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
    def test_gitleaks_not_installed_returns_empty(self, tmp_path):
        """If gitleaks is not installed, gracefully return empty findings."""
        scanner = GitleaksScanner()
        with patch("subprocess.run", side_effect=FileNotFoundError("gitleaks not found")):
            findings = scanner.scan(str(tmp_path))
        assert findings == []

    def test_gitleaks_crash_returns_empty(self, tmp_path):
        """If gitleaks crashes with unexpected exit code, return empty findings."""
        import subprocess
        scanner = GitleaksScanner()
        mock_result = MagicMock()
        mock_result.returncode = 2  # Unexpected error, not 0 (clean) or 1 (leak)
        mock_result.stderr = "fatal error"
        with patch("subprocess.run", return_value=mock_result):
            findings = scanner.scan(str(tmp_path))
        assert findings == []

    def test_gitleaks_clean_returns_empty(self, tmp_path):
        """A clean directory with no secrets returns zero findings."""
        scanner = GitleaksScanner()
        # Write a totally innocuous file
        (tmp_path / "readme.txt").write_text("This is a clean file with no secrets.")

        # Mock gitleaks returning an empty JSON array (no leaks)
        mock_result = MagicMock()
        mock_result.returncode = 0
        empty_report = []
        with patch("subprocess.run", return_value=mock_result), \
             patch("builtins.open", create=True) as mock_open, \
             patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=0):  # zero size => no findings
            findings = scanner.scan(str(tmp_path))
        assert findings == []

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
        import tempfile, os

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(gitleaks_report, f)
            report_path = f.name

        mock_result = MagicMock()
        mock_result.returncode = 1  # gitleaks exits 1 when findings exist

        def fake_run(cmd, **kwargs):
            # Copy the fake report into the path gitleaks would write to
            for i, arg in enumerate(cmd):
                if arg == "--report-path" and i + 1 < len(cmd):
                    import shutil
                    shutil.copy(report_path, cmd[i + 1])
            return mock_result

        with patch("subprocess.run", side_effect=fake_run):
            findings = scanner.scan(str(tmp_path))

        os.unlink(report_path)

        assert len(findings) == 1
        finding = findings[0]
        assert finding.type == "SECRET"
        assert finding.scanner == "gitleaks"
        assert finding.rule_id == "generic-api-key"
        # The raw secret value must NOT appear in the evidence
        assert fake_secret not in (finding.evidence or "")
        # Masked marker should be present
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
            findings = scanner.scan(NODE_DEP_DIR)
        assert isinstance(findings, list)

    def test_recognizes_requirements_txt(self):
        """OSV scanner should detect requirements.txt files."""
        scanner = OSVScanner()
        mock_osv_response = MagicMock()
        mock_osv_response.status_code = 200
        mock_osv_response.json.return_value = {"results": [{"vulns": []}, {"vulns": []}]}

        with patch("httpx.post", return_value=mock_osv_response):
            findings = scanner.scan(PYTHON_DEP_DIR)
        assert isinstance(findings, list)

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
            findings = scanner.scan(NODE_DEP_DIR)

        assert len(findings) >= 1
        f = findings[0]
        assert f.type == "DEPENDENCY"
        assert f.scanner == "osv"
        assert "GHSA-xxxx-yyyy-zzzz" in f.rule_id

    def test_osv_failure_handled_gracefully(self, tmp_path):
        """If OSV API is unavailable, return empty findings and don't crash."""
        scanner = OSVScanner()
        # Write a requirements.txt so there are queries to send
        (tmp_path / "requirements.txt").write_text("requests==2.20.0\n")

        with patch("httpx.post", side_effect=Exception("OSV unavailable")):
            findings = scanner.scan(str(tmp_path))
        assert findings == []

    def test_malformed_dependency_file_handled(self, tmp_path):
        """Malformed package.json should not crash the scanner."""
        scanner = OSVScanner()
        (tmp_path / "package.json").write_text("this is not valid json {{{")

        mock_osv_response = MagicMock()
        mock_osv_response.status_code = 200
        mock_osv_response.json.return_value = {"results": []}

        with patch("httpx.post", return_value=mock_osv_response):
            findings = scanner.scan(str(tmp_path))
        # Should return empty, no crash
        assert findings == []

    def test_empty_directory_returns_empty(self, tmp_path):
        """A directory with no manifest files returns empty findings without querying OSV."""
        scanner = OSVScanner()
        with patch("httpx.post") as mock_post:
            findings = scanner.scan(str(tmp_path))
        # Should not have called OSV at all
        mock_post.assert_not_called()
        assert findings == []
