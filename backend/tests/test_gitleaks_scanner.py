"""
Unit and integration tests for Gitleaks secret scanner adapter.
"""
import json
import os
import subprocess
from unittest.mock import patch, MagicMock
from app.scanners.secrets.gitleaks import GitleaksScanner


def test_gitleaks_handles_missing_executable(tmp_path):
    with patch("subprocess.run", side_effect=FileNotFoundError):
        scanner = GitleaksScanner()
        res = scanner.scan(str(tmp_path))

        assert res.executed is False
        assert res.status == "FAILED"
        assert "not found" in res.error_message.lower()
        assert len(res.findings) == 0


def test_gitleaks_parses_findings_and_masks_secrets(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("AWS_SECRET_KEY=AKIAIOSFODNN7EXAMPLE\n")

    fake_report = [
        {
            "RuleID": "aws-access-token",
            "Description": "AWS Access Token leak",
            "Secret": "AKIAIOSFODNN7EXAMPLE",
            "File": ".env",
            "StartLine": 1
        }
    ]

    mock_version = MagicMock(returncode=0, stdout="v8.18.2")

    def mock_subprocess_run(cmd, **kwargs):
        if "version" in cmd:
            return mock_version
        # For gitleaks detect command
        report_path = cmd[cmd.index("--report-path") + 1]
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(fake_report, f)
        return MagicMock(returncode=1, stderr="")

    with patch("subprocess.run", side_effect=mock_subprocess_run):
        scanner = GitleaksScanner()
        res = scanner.scan(str(tmp_path))

    assert res.executed is True
    assert res.status == "COMPLETED_WITH_FINDINGS"
    assert len(res.findings) == 1

    f = res.findings[0]
    assert f.type == "SECRET"
    assert f.rule_id == "aws-access-token"
    assert f.file_path == ".env"
    assert f.line_number == 1
    # Verify strict secret masking
    assert "AKIAIOSFODNN7EXAMPLE" not in f.evidence
    assert "AKIA********" in f.evidence
