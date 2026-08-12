import json
import logging
import subprocess
import tempfile
import os
from typing import List

from ..base import BaseScanner, FindingData

logger = logging.getLogger(__name__)

class GitleaksScanner(BaseScanner):
    def scan(self, repository_path: str) -> List[FindingData]:
        findings = []
        
        # Check if gitleaks is installed
        try:
            subprocess.run(["gitleaks", "version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("Gitleaks is not installed or not in PATH. Skipping secret scan.")
            return findings

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            report_path = tmp_file.name

        try:
            # Run gitleaks with --no-git to just scan the files in the directory
            cmd = [
                "gitleaks", "detect", 
                "--no-git",
                "--report-format", "json",
                "--report-path", report_path,
                "--source", repository_path,
                "--exit-code", "0"  # Prevent gitleaks from exiting with 1 when finding leaks
            ]
            
            # Use exit-code 0 so we don't throw CalledProcessError on leaks.
            # But gitleaks exit code is 1 on leaks. We can just ignore the exit code if it's 1.
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode not in (0, 1):
                logger.error(f"Gitleaks failed with exit code {result.returncode}: {result.stderr}")
                return findings

            if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
                with open(report_path, "r", encoding="utf-8") as f:
                    raw_findings = json.load(f)
                    
                for raw in raw_findings:
                    secret_val = raw.get("Secret", "")
                    masked_evidence = f"{secret_val[:4]}********" if len(secret_val) > 4 else "********"
                    
                    finding = FindingData(
                        type="SECRET",
                        severity="HIGH", # Default severity for secrets
                        title="Potential secret detected",
                        scanner="gitleaks",
                        description=raw.get("Description", "A hardcoded secret was found."),
                        file_path=raw.get("File", ""),
                        line_number=raw.get("StartLine", 0),
                        rule_id=raw.get("RuleID", ""),
                        evidence=f"Secret matches rule {raw.get('RuleID')}: {masked_evidence}",
                        recommendation="Revoke this secret, rotate it, and remove it from the repository."
                    )
                    findings.append(finding)
        except Exception as e:
            logger.error(f"Error during Gitleaks scan: {e}")
        finally:
            if os.path.exists(report_path):
                os.remove(report_path)

        return findings
