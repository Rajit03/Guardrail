import json
import logging
import os
import subprocess
import tempfile
from typing import List

from app.scanners.base import FindingData, ScannerResult
from app.scanners.secrets.scanner import BaseSecretScanner

logger = logging.getLogger(__name__)


class GitleaksScanner(BaseSecretScanner):
    """
    Scanner adapter for Gitleaks.
    Performs static secret scanning across all repository files recursively.
    """

    def scan(self, repository_path: str) -> ScannerResult:
        findings: List[FindingData] = []

        # Check if gitleaks is installed in execution environment
        try:
            version_check = subprocess.run(
                ["gitleaks", "version"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            logger.info(f"Gitleaks version check output: {version_check.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            err_msg = "Gitleaks executable not found on system PATH. Secret scanning failed."
            logger.error(err_msg)
            return ScannerResult(
                scanner_name="gitleaks",
                executed=False,
                status="FAILED",
                error_message=err_msg,
                raw_findings_count=0,
                normalized_findings_count=0,
                findings=[]
            )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            report_path = tmp_file.name

        try:
            # Command to scan all files recursively without git repository history
            cmd = [
                "gitleaks",
                "detect",
                "--no-git",
                "--report-format",
                "json",
                "--report-path",
                report_path,
                "--source",
                repository_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            # Exit code 0 = no leaks found; exit code 1 = leaks detected; others = failure
            if result.returncode not in (0, 1):
                err_msg = f"Gitleaks execution failed with exit code {result.returncode}: {result.stderr.strip()}"
                logger.error(err_msg)
                return ScannerResult(
                    scanner_name="gitleaks",
                    executed=True,
                    status="FAILED",
                    error_message=err_msg[:1024],
                    raw_findings_count=0,
                    normalized_findings_count=0,
                    findings=[]
                )

            raw_findings_count = 0
            if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
                with open(report_path, "r", encoding="utf-8") as f:
                    raw_findings = json.load(f)

                if isinstance(raw_findings, list):
                    raw_findings_count = len(raw_findings)
                    for raw in raw_findings:
                        if not isinstance(raw, dict):
                            continue

                        secret_val = raw.get("Secret", "")
                        rule_id = raw.get("RuleID", "generic-secret")

                        # Mask secret value completely to prevent credential exposure
                        if len(secret_val) > 4:
                            masked_evidence = f"{secret_val[:4]}********"
                        else:
                            masked_evidence = "********"

                        rel_file_path = raw.get("File", "")
                        # Normalize path separators for Windows/Linux consistency
                        rel_file_path = rel_file_path.replace("\\", "/")
                        if rel_file_path.startswith(repository_path.replace("\\", "/")):
                            rel_file_path = os.path.relpath(rel_file_path, repository_path).replace("\\", "/")

                        finding = FindingData(
                            type="SECRET",
                            severity="HIGH",  # Base severity for static credential findings
                            title=f"Potential secret detected ({rule_id})",
                            scanner="gitleaks",
                            description=raw.get("Description", "A hardcoded secret or sensitive credential was detected."),
                            file_path=rel_file_path,
                            line_number=raw.get("StartLine", 0),
                            rule_id=rule_id,
                            evidence=f"Matches secret rule '{rule_id}': {masked_evidence}",
                            recommendation="Rotate and revoke the credential immediately, and remove it from source control."
                        )
                        findings.append(finding)

            return ScannerResult(
                scanner_name="gitleaks",
                executed=True,
                status="COMPLETED",
                error_message=None,
                raw_findings_count=raw_findings_count,
                normalized_findings_count=len(findings),
                deduplicated_findings_count=len(findings),
                findings=findings
            )

        except json.JSONDecodeError as e:
            err_msg = f"Failed to parse Gitleaks report JSON output: {e}"
            logger.error(err_msg)
            return ScannerResult(
                scanner_name="gitleaks",
                executed=True,
                status="FAILED",
                error_message=err_msg,
                findings=[]
            )
        except subprocess.TimeoutExpired:
            err_msg = "Gitleaks scan timed out after 120 seconds."
            logger.error(err_msg)
            return ScannerResult(
                scanner_name="gitleaks",
                executed=True,
                status="FAILED",
                error_message=err_msg,
                findings=[]
            )
        except Exception as e:
            err_msg = f"Unexpected error during Gitleaks scan: {e}"
            logger.error(err_msg)
            return ScannerResult(
                scanner_name="gitleaks",
                executed=True,
                status="FAILED",
                error_message=err_msg[:1024],
                findings=[]
            )
        finally:
            if os.path.exists(report_path):
                try:
                    os.remove(report_path)
                except OSError:
                    pass
