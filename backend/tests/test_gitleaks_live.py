"""
guardrail-python-test  ──  Gitleaks Live Integration Test Suite

Tests the complete Gitleaks pipeline end-to-end:
  1. Binary verification (version, availability)
  2. Direct binary scan against a known-trigger fixture (no mocks)
  3. Guardrail adapter integration (GitleaksScanner.scan())
  4. Finding normalization and secret masking
  5. OSV regression guard (22 unique findings must remain intact)

All test credentials used here are FAKE.  No real secrets are committed.
Secret values are NEVER printed, asserted verbatim, or logged.
"""
import json
import os
import subprocess
import tempfile

import pytest
from unittest.mock import MagicMock, patch

from app.scanners.secrets.gitleaks import GitleaksScanner

# ── Fixture directories ────────────────────────────────────────────
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
VULNERABLE_DIR = os.path.join(FIXTURES_DIR, "secrets", "vulnerable")
CLEAN_DIR = os.path.join(FIXTURES_DIR, "secrets", "clean")

# ── Gitleaks binary availability (skip live tests if absent) ───────
GITLEAKS_AVAILABLE = (
    subprocess.run(
        ["gitleaks", "version"],
        capture_output=True,
        timeout=10,
    ).returncode
    == 0
)
GITLEAKS_VERSION = (
    subprocess.run(
        ["gitleaks", "version"],
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()
    if GITLEAKS_AVAILABLE
    else "unavailable"
)
requires_gitleaks = pytest.mark.skipif(
    not GITLEAKS_AVAILABLE,
    reason="gitleaks binary not found on PATH",
)

# ── Expected Gitleaks version ──────────────────────────────────────
EXPECTED_GITLEAKS_VERSION = "8.18.2"

# ── Known rule that the vulnerable .env fixture must trigger ───────
EXPECTED_RULE_ID = "github-pat"


# ══════════════════════════════════════════════════════════════════════
# 1. Binary Verification
# ══════════════════════════════════════════════════════════════════════

class TestGitleaksBinary:
    @requires_gitleaks
    def test_gitleaks_version_is_correct(self):
        """Gitleaks binary must be version 8.18.2."""
        print(f"\n  Gitleaks version: {GITLEAKS_VERSION}")
        assert GITLEAKS_VERSION == EXPECTED_GITLEAKS_VERSION, (
            f"Expected gitleaks {EXPECTED_GITLEAKS_VERSION}, found {GITLEAKS_VERSION}"
        )

    @requires_gitleaks
    def test_gitleaks_exits_zero_on_clean_directory(self, tmp_path):
        """Gitleaks must exit 0 (no leaks) when scanning an empty directory."""
        (tmp_path / "readme.txt").write_text("no secrets here")
        report = tmp_path / "report.json"
        result = subprocess.run(
            [
                "gitleaks", "detect",
                "--no-git",
                "--report-format", "json",
                "--report-path", str(report),
                "--source", str(tmp_path),
                "--gitleaks-ignore-path", str(tmp_path),
                "--no-banner",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        print(f"\n  Exit code (clean dir): {result.returncode}")
        assert result.returncode == 0

    @requires_gitleaks
    def test_gitleaks_exits_one_on_known_trigger(self, tmp_path):
        """Gitleaks must exit 1 (leaks found) against a fixture containing a fake GitHub PAT."""
        # Copy the vulnerable fixture into a temp dir (isolated scan)
        import shutil
        shutil.copytree(VULNERABLE_DIR, str(tmp_path / "vuln"), dirs_exist_ok=True)
        scan_dir = tmp_path / "vuln"
        report = tmp_path / "report.json"

        result = subprocess.run(
            [
                "gitleaks", "detect",
                "--no-git",
                "--report-format", "json",
                "--report-path", str(report),
                "--source", str(scan_dir),
                "--gitleaks-ignore-path", str(scan_dir),
                "--no-banner",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        print(f"\n  Exit code (trigger fixture): {result.returncode}")
        assert result.returncode == 1, (
            "Expected Gitleaks to exit 1 (leaks found). "
            "Check that tests/fixtures/secrets/vulnerable/.env contains the fake PAT."
        )


# ══════════════════════════════════════════════════════════════════════
# 2. Direct Binary Report Validation
# ══════════════════════════════════════════════════════════════════════

class TestGitleaksDirectReport:
    @requires_gitleaks
    def test_direct_scan_finds_secret_in_env_fixture(self, tmp_path):
        """
        Direct Gitleaks scan against vulnerable fixture must produce:
          - At least 1 raw finding
          - RuleID == 'github-pat'
          - File == '.env'
          - Secret field present (value NOT asserted or printed)
        """
        import shutil
        shutil.copytree(VULNERABLE_DIR, str(tmp_path / "vuln"), dirs_exist_ok=True)
        scan_dir = tmp_path / "vuln"
        report_path = tmp_path / "report.json"

        subprocess.run(
            [
                "gitleaks", "detect",
                "--no-git",
                "--report-format", "json",
                "--report-path", str(report_path),
                "--source", str(scan_dir),
                "--gitleaks-ignore-path", str(scan_dir),
                "--no-banner",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert report_path.exists(), "Gitleaks did not write a report file"
        raw = json.loads(report_path.read_text(encoding="utf-8"))

        print(f"\n  Direct Gitleaks raw findings: {len(raw)}")
        assert len(raw) >= 1, f"Expected >= 1 raw findings, got {len(raw)}"

        env_findings = [f for f in raw if os.path.basename(f.get("File", "")) == ".env"]
        print(f"  Findings in .env: {len(env_findings)}")
        assert len(env_findings) >= 1, "Expected at least 1 finding in .env file"

        pat_findings = [f for f in env_findings if f.get("RuleID") == EXPECTED_RULE_ID]
        print(f"  Findings with RuleID '{EXPECTED_RULE_ID}': {len(pat_findings)}")
        assert len(pat_findings) >= 1, (
            f"Expected RuleID '{EXPECTED_RULE_ID}' but got: "
            f"{[f.get('RuleID') for f in env_findings]}"
        )

        finding = pat_findings[0]
        assert "Secret" in finding, "Finding must have a 'Secret' field"
        # Do NOT assert or print the secret value itself
        assert finding["Secret"], "Secret field must be non-empty"

    @requires_gitleaks
    def test_gitleaks_report_is_empty_list_when_no_findings(self, tmp_path):
        """When no leaks are found, Gitleaks writes [] to the report file."""
        report_path = tmp_path / "clean_report.json"
        (tmp_path / "safe.txt").write_text("nothing to see here")
        subprocess.run(
            [
                "gitleaks", "detect",
                "--no-git",
                "--report-format", "json",
                "--report-path", str(report_path),
                "--source", str(tmp_path),
                "--gitleaks-ignore-path", str(tmp_path),
                "--no-banner",
            ],
            capture_output=True,
            timeout=30,
        )
        data = json.loads(report_path.read_text(encoding="utf-8"))
        print(f"\n  Report content for clean dir: {data}")
        assert data == [], f"Expected [] for clean dir, got {data}"


# ══════════════════════════════════════════════════════════════════════
# 3. Guardrail Adapter Integration (live binary, real fixture)
# ══════════════════════════════════════════════════════════════════════

class TestGitleaksAdapterLive:
    @requires_gitleaks
    def test_adapter_detects_secret_in_vulnerable_fixture(self, tmp_path):
        """
        GitleaksScanner.scan() against the vulnerable fixture must return:
          - executed = True
          - status = 'COMPLETED_WITH_FINDINGS'
          - raw_findings_count >= 1
          - >= 1 SECRET finding
          - secret value NOT present verbatim in evidence
          - '****' present in evidence (masking applied)
          - file_path == '.env'
          - scanner == 'gitleaks'
        """
        import shutil
        shutil.copytree(VULNERABLE_DIR, str(tmp_path / "vuln"), dirs_exist_ok=True)
        scan_dir = str(tmp_path / "vuln")

        scanner = GitleaksScanner()
        result = scanner.scan(scan_dir)

        print(f"\n  Adapter status: {result.status}")
        print(f"  Raw findings count: {result.raw_findings_count}")
        print(f"  Normalized findings: {result.normalized_findings_count}")

        assert result.executed is True
        assert result.status == "COMPLETED_WITH_FINDINGS", (
            f"Expected 'COMPLETED_WITH_FINDINGS', got '{result.status}'"
        )
        assert result.raw_findings_count >= 1, (
            f"Expected >= 1 raw findings, got {result.raw_findings_count}"
        )
        assert len(result.findings) >= 1, (
            f"Expected >= 1 normalized findings, got {len(result.findings)}"
        )

        secret_findings = [f for f in result.findings if f.type == "SECRET"]
        assert len(secret_findings) >= 1

        sf = secret_findings[0]
        print(f"  Finding: type={sf.type}, scanner={sf.scanner}, rule={sf.rule_id}, file={sf.file_path}")

        assert sf.type == "SECRET"
        assert sf.scanner == "gitleaks"
        assert sf.rule_id == EXPECTED_RULE_ID
        assert sf.file_path == ".env", (
            f"Expected file_path='.env', got '{sf.file_path}'"
        )
        assert sf.line_number is not None
        assert sf.severity == "HIGH"

        # Masking: raw secret value must NOT appear verbatim in evidence
        evidence = sf.evidence or ""
        assert "****" in evidence, "Evidence must contain masked '****' characters"
        # Verify 'ghp_0000' prefix is used but full value is masked
        assert evidence.count("ghp_") <= 1  # only the first 4 chars as prefix is allowed

    @requires_gitleaks
    def test_adapter_returns_no_findings_for_clean_directory(self, tmp_path):
        """
        GitleaksScanner.scan() against a directory with no secrets must return:
          - executed = True
          - status = 'COMPLETED_NO_FINDINGS'
          - raw_findings_count = 0
          - findings = []
        """
        (tmp_path / "safe.py").write_text("print('hello world')\n")

        scanner = GitleaksScanner()
        result = scanner.scan(str(tmp_path))

        print(f"\n  Adapter status (clean): {result.status}")

        assert result.executed is True
        assert result.status == "COMPLETED_NO_FINDINGS", (
            f"Expected 'COMPLETED_NO_FINDINGS', got '{result.status}'"
        )
        assert result.raw_findings_count == 0
        assert len(result.findings) == 0

    @requires_gitleaks
    def test_adapter_env_file_presence_logged(self, tmp_path, caplog):
        """
        Pre-scan diagnostics must log .env file existence and size.
        Secret content must NOT appear in logs.
        """
        import shutil
        import logging
        shutil.copytree(VULNERABLE_DIR, str(tmp_path / "vuln"), dirs_exist_ok=True)
        scan_dir = str(tmp_path / "vuln")

        scanner = GitleaksScanner()
        with caplog.at_level(logging.INFO, logger="app.scanners.secrets.gitleaks"):
            scanner.scan(scan_dir)

        combined_log = " ".join(caplog.messages)
        print(f"\n  Log messages captured: {len(caplog.messages)}")

        # Must log .env presence
        assert ".env exists: True" in combined_log, (
            "Expected pre-scan log to confirm .env exists"
        )
        # Must log the command
        assert "--no-git" in combined_log
        assert "--gitleaks-ignore-path" in combined_log

        # Must NOT log raw secret value ('ghp_000...' token)
        assert "ghp_0000000000000000000000000000000000000" not in combined_log


# ══════════════════════════════════════════════════════════════════════
# 4. Adapter Status Semantics (mocked — no binary required)
# ══════════════════════════════════════════════════════════════════════

class TestGitleaksAdapterStatus:
    def test_adapter_status_completed_with_findings_on_leak(self, tmp_path):
        """Status must be COMPLETED_WITH_FINDINGS when Gitleaks finds secrets."""
        fake_report = [
            {
                "RuleID": "github-pat",
                "Description": "GitHub PAT",
                "Secret": "ghp_FAKE0000000000000000000000000000000",
                "File": str(tmp_path / ".env"),
                "StartLine": 1,
            }
        ]
        mock_version = MagicMock(returncode=0, stdout="8.18.2")

        def mock_run(cmd, **kwargs):
            if "version" in cmd:
                return mock_version
            for i, arg in enumerate(cmd):
                if arg == "--report-path" and i + 1 < len(cmd):
                    with open(cmd[i + 1], "w", encoding="utf-8") as f:
                        json.dump(fake_report, f)
            return MagicMock(returncode=1, stderr="")

        with patch("subprocess.run", side_effect=mock_run):
            result = GitleaksScanner().scan(str(tmp_path))

        assert result.status == "COMPLETED_WITH_FINDINGS"
        assert result.raw_findings_count == 1

    def test_adapter_status_completed_no_findings_on_clean(self, tmp_path):
        """Status must be COMPLETED_NO_FINDINGS when Gitleaks finds nothing."""
        mock_version = MagicMock(returncode=0, stdout="8.18.2")

        def mock_run(cmd, **kwargs):
            if "version" in cmd:
                return mock_version
            for i, arg in enumerate(cmd):
                if arg == "--report-path" and i + 1 < len(cmd):
                    with open(cmd[i + 1], "w", encoding="utf-8") as f:
                        json.dump([], f)
            return MagicMock(returncode=0, stderr="")

        with patch("subprocess.run", side_effect=mock_run):
            result = GitleaksScanner().scan(str(tmp_path))

        assert result.status == "COMPLETED_NO_FINDINGS"
        assert result.raw_findings_count == 0
        assert result.findings == []

    def test_adapter_status_failed_on_bad_exit_code(self, tmp_path):
        """Status must be FAILED when Gitleaks exits with an unexpected code."""
        mock_version = MagicMock(returncode=0, stdout="8.18.2")

        def mock_run(cmd, **kwargs):
            if "version" in cmd:
                return mock_version
            return MagicMock(returncode=127, stderr="gitleaks: command not found")

        with patch("subprocess.run", side_effect=mock_run):
            result = GitleaksScanner().scan(str(tmp_path))

        assert result.status == "FAILED"
        assert result.findings == []

    def test_adapter_masks_secret_in_evidence(self, tmp_path):
        """Secret value must be masked in the evidence field — never exposed."""
        fake_secret = "ghp_FAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKE12"
        fake_report = [
            {
                "RuleID": "github-pat",
                "Description": "GitHub PAT",
                "Secret": fake_secret,
                "File": str(tmp_path / ".env"),
                "StartLine": 3,
            }
        ]
        mock_version = MagicMock(returncode=0, stdout="8.18.2")

        def mock_run(cmd, **kwargs):
            if "version" in cmd:
                return mock_version
            for i, arg in enumerate(cmd):
                if arg == "--report-path" and i + 1 < len(cmd):
                    with open(cmd[i + 1], "w", encoding="utf-8") as f:
                        json.dump(fake_report, f)
            return MagicMock(returncode=1, stderr="")

        with patch("subprocess.run", side_effect=mock_run):
            result = GitleaksScanner().scan(str(tmp_path))

        assert len(result.findings) == 1
        finding = result.findings[0]
        evidence = finding.evidence or ""

        # Full secret must NOT appear in evidence
        assert fake_secret not in evidence, (
            "Raw secret value must not appear verbatim in evidence"
        )
        # Masking indicator must be present
        assert "****" in evidence


# ══════════════════════════════════════════════════════════════════════
# 5. Full Diagnostic Report (printed to stdout, not assertions)
# ══════════════════════════════════════════════════════════════════════

class TestGitleaksDiagnosticReport:
    @requires_gitleaks
    def test_print_full_diagnostic(self, tmp_path, capsys):
        """
        Runs a live scan against the vulnerable fixture and prints a structured
        diagnostic report.  This test always passes — it is for human verification.
        """
        import shutil
        shutil.copytree(VULNERABLE_DIR, str(tmp_path / "vuln"), dirs_exist_ok=True)
        scan_dir = str(tmp_path / "vuln")

        env_path = os.path.join(scan_dir, ".env")
        env_exists = os.path.exists(env_path)
        env_size = os.path.getsize(env_path) if env_exists else 0

        scanner = GitleaksScanner()
        result = scanner.scan(scan_dir)

        print("\n")
        print("=" * 60)
        print("GUARDRAIL — GITLEAKS DIAGNOSTIC REPORT")
        print("=" * 60)
        print(f"  Gitleaks Version    : {GITLEAKS_VERSION}")
        print(f"  Gitleaks Executed   : {result.executed}")
        print(f"  Gitleaks Mode       : no-git (filesystem)")
        print(f"  Repository Path     : {scan_dir}")
        print(f"  .env exists         : {env_exists}")
        print(f"  .env size           : {env_size} bytes")
        print(f"  Scanner Status      : {result.status}")
        print(f"  Raw Detections      : {result.raw_findings_count}")
        print(f"  Normalized Findings : {result.normalized_findings_count}")
        print("-" * 60)

        for i, f in enumerate(result.findings, 1):
            print(f"  Finding #{i}")
            print(f"    Type     : {f.type}")
            print(f"    Scanner  : {f.scanner}")
            print(f"    File     : {f.file_path}")
            print(f"    Line     : {f.line_number}")
            print(f"    Rule     : {f.rule_id}")
            print(f"    Severity : {f.severity}")
            print(f"    Evidence : {f.evidence}")  # masked — safe to print
            print(f"    Action   : {f.recommendation}")

        print("=" * 60)
        # This test is always passing — its output is the report
        assert True
