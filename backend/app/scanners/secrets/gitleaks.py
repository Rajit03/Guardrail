import json
import logging
import os
import subprocess
import tempfile
from typing import List

from app.scanners.base import FindingData
from app.scanners.secrets.scanner import BaseSecretScanner

logger = logging.getLogger(__name__)


class GitleaksScanner(BaseSecretScanner):
    """
    Scanner adapter for Gitleaks.
    Performs static secret scanning without executing repository code.
    """

    def scan(self, repository_path: str) -> List[FindingData]:
        findings: List[FindingData] = []

        # Check if gitleaks is installed
        try:
            subprocess.run(
                ["gitleaks", "version"],
                check=True,
                capture_output=True,
                timeout=10
            )
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("Gitleaks is not installed or not available in PATH. Skipping secret scan.")
            return findings

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            report_path = tmp_file.name

        try:
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

            # Exit code 0 means no leaks; 1 means leaks found; any other exit code is an error
            if result.returncode not in (0, 1):
                logger.error(f"Gitleaks scan failed with exit code {result.returncode}: {result.stderr}")
                return findings

            if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
                with open(report_path, "r", encoding="utf-8") as f:
                    raw_findings = json.load(f)

                if not isinstance(raw_findings, list):
                    logger.warning("Unexpected non-list Gitleaks report format.")
                    return findings

                for raw in raw_findings:
                    if not isinstance(raw, dict):
                        continue
                    secret_val = raw.get("Secret", "")
                    rule_id = raw.get("RuleID", "generic-secret")

                    # Always mask secret value to prevent credential leaks
                    if len(secret_val) > 4:
                        masked_evidence = f"{secret_val[:4]}********"
                    else:
                        masked_evidence = "********"

                    finding = FindingData(
                        type="SECRET",
                        severity="HIGH",  # Deterministic mapping for secret detections
                        title=f"Potential secret detected ({rule_id})",
                        scanner="gitleaks",
                        description=raw.get("Description", "A potential credential or hardcoded secret was found."),
                        file_path=raw.get("File", ""),
                        line_number=raw.get("StartLine", 0),
                        rule_id=rule_id,
                        evidence=f"Secret matches rule '{rule_id}': {masked_evidence}",
                        recommendation="Revoke the credential immediately, rotate affected systems, and remove it from source control history."
                    )
                    findings.append(finding)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gitleaks report JSON: {e}")
        except subprocess.TimeoutExpired:
            logger.error("Gitleaks scan timed out after 120 seconds.")
        except Exception as e:
            logger.error(f"Error during Gitleaks scan: {e}")
        finally:
            if os.path.exists(report_path):
                try:
                    os.remove(report_path)
                except OSError:
                    pass

        return findings
