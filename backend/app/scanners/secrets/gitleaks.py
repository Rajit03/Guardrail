import json
import logging
import os
import subprocess
import tempfile
from typing import List

from app.scanners.base import FindingData, ScannerResult
from app.scanners.secrets.scanner import BaseSecretScanner

logger = logging.getLogger(__name__)

SCAN_MODE = "no-git"


class GitleaksScanner(BaseSecretScanner):
    """
    Scanner adapter for Gitleaks.
    Performs static secret scanning across all repository files recursively
    using `gitleaks detect --no-git` (filesystem scan, no git history).
    """

    def scan(self, repository_path: str) -> ScannerResult:
        findings: List[FindingData] = []
        gitleaks_version = "unknown"

        # ── 1. Verify Gitleaks binary ─────────────────────────────────
        try:
            version_check = subprocess.run(
                ["gitleaks", "version"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            gitleaks_version = version_check.stdout.strip()
            logger.info(f"[Gitleaks] Version: {gitleaks_version}")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            err_msg = "Gitleaks executable not found on system PATH. Secret scanning failed."
            logger.error(f"[Gitleaks] {err_msg}")
            return ScannerResult(
                scanner_name="gitleaks",
                executed=False,
                status="FAILED",
                error_message=err_msg,
                raw_findings_count=0,
                normalized_findings_count=0,
                findings=[],
            )

        # ── 2. Pre-scan repository diagnostics (no content logged) ────
        repo_file_count = 0
        hidden_file_count = 0
        env_file_exists = False
        env_file_size = 0
        try:
            for root, dirs, files in os.walk(repository_path):
                dirs[:] = [d for d in dirs if d != ".git"]
                for fname in files:
                    repo_file_count += 1
                    if fname.startswith("."):
                        hidden_file_count += 1
                    if fname.lower() == ".env" or fname.lower().startswith(".env."):
                        env_file_exists = True
                        try:
                            env_file_size = os.path.getsize(
                                os.path.join(root, fname)
                            )
                        except OSError:
                            pass
            logger.info(
                f"[Gitleaks] Pre-scan | Repository: {repository_path} | "
                f".env exists: {env_file_exists} | .env size: {env_file_size} bytes | "
                f"Total files: {repo_file_count} | Hidden files: {hidden_file_count}"
            )
        except Exception as diag_err:
            logger.warning(f"[Gitleaks] Pre-scan diagnostic failed: {diag_err}")

        # ── 3. Build Gitleaks command ─────────────────────────────────
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            report_path = tmp_file.name

        # Point --gitleaks-ignore-path at the source directory so Gitleaks
        # searches for .gitleaksignore in the scanned repo itself (not /app CWD).
        cmd = [
            "gitleaks",
            "detect",
            "--no-git",
            "--report-format", "json",
            "--report-path", report_path,
            "--source", repository_path,
            "--gitleaks-ignore-path", repository_path,
            "--no-banner",
        ]

        logger.info(f"[Gitleaks] Command: {' '.join(cmd)}")
        logger.info(f"[Gitleaks] Scan mode: {SCAN_MODE}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Gitleaks 8.18.2 exit-code semantics:
            #   0 = scan completed, no leaks found
            #   1 = scan completed, leaks detected
            #   other values = fatal error / misconfiguration
            logger.info(
                f"[Gitleaks] Exit code: {result.returncode} | "
                f"stderr: {result.stderr.strip()[:300]}"
            )

            if result.returncode not in (0, 1):
                err_msg = (
                    f"Gitleaks execution failed with exit code {result.returncode}: "
                    f"{result.stderr.strip()}"
                )
                logger.error(f"[Gitleaks] {err_msg}")
                return ScannerResult(
                    scanner_name="gitleaks",
                    executed=True,
                    status="FAILED",
                    error_message=err_msg[:1024],
                    raw_findings_count=0,
                    normalized_findings_count=0,
                    findings=[],
                )

            # ── 4. Parse report ───────────────────────────────────────
            raw_findings_count = 0
            report_exists = os.path.exists(report_path)
            report_size = os.path.getsize(report_path) if report_exists else 0
            logger.info(
                f"[Gitleaks] Report: {report_path} | "
                f"exists: {report_exists} | size: {report_size} bytes"
            )

            if report_exists and report_size > 0:
                with open(report_path, "r", encoding="utf-8") as f:
                    raw_findings = json.load(f)

                if isinstance(raw_findings, list):
                    raw_findings_count = len(raw_findings)
                    logger.info(
                        f"[Gitleaks] Raw findings in report: {raw_findings_count}"
                    )

                    for raw in raw_findings:
                        if not isinstance(raw, dict):
                            continue

                        secret_val = raw.get("Secret", "")
                        rule_id = raw.get("RuleID", "generic-secret")

                        # Mask secret — never expose credential values in logs/API
                        masked_evidence = (
                            f"{secret_val[:4]}********"
                            if len(secret_val) > 4
                            else "********"
                        )

                        raw_file = raw.get("File", "")
                        # Gitleaks returns absolute paths; normalise to repo-relative
                        rel_file_path = raw_file.replace("\\", "/")
                        repo_norm = repository_path.replace("\\", "/")
                        if rel_file_path.startswith(repo_norm):
                            rel_file_path = os.path.relpath(
                                raw_file, repository_path
                            ).replace("\\", "/")

                        findings.append(
                            FindingData(
                                type="SECRET",
                                severity="HIGH",
                                title=f"Potential secret detected ({rule_id})",
                                scanner="gitleaks",
                                description=raw.get(
                                    "Description",
                                    "A hardcoded secret or sensitive credential was detected.",
                                ),
                                file_path=rel_file_path,
                                line_number=raw.get("StartLine", 0),
                                rule_id=rule_id,
                                evidence=f"Matches secret rule '{rule_id}': {masked_evidence}",
                                recommendation=(
                                    "Rotate and revoke the credential immediately, "
                                    "and remove it from source control."
                                ),
                            )
                        )

            # ── 5. Return result with fine-grained status ─────────────
            # Distinguish: findings present vs scan clean vs failure.
            if raw_findings_count > 0:
                completed_status = "COMPLETED_WITH_FINDINGS"
            else:
                completed_status = "COMPLETED_NO_FINDINGS"

            logger.info(
                f"[Gitleaks] Done | Status: {completed_status} | "
                f"Mode: {SCAN_MODE} | Version: {gitleaks_version} | "
                f"Raw: {raw_findings_count} | Normalized: {len(findings)}"
            )

            return ScannerResult(
                scanner_name="gitleaks",
                executed=True,
                status=completed_status,
                error_message=None,
                raw_findings_count=raw_findings_count,
                normalized_findings_count=len(findings),
                deduplicated_findings_count=len(findings),
                findings=findings,
            )

        except json.JSONDecodeError as e:
            err_msg = f"Failed to parse Gitleaks report JSON: {e}"
            logger.error(f"[Gitleaks] {err_msg}")
            return ScannerResult(
                scanner_name="gitleaks",
                executed=True,
                status="FAILED",
                error_message=err_msg,
                findings=[],
            )
        except subprocess.TimeoutExpired:
            err_msg = "Gitleaks scan timed out after 120 seconds."
            logger.error(f"[Gitleaks] {err_msg}")
            return ScannerResult(
                scanner_name="gitleaks",
                executed=True,
                status="FAILED",
                error_message=err_msg,
                findings=[],
            )
        except Exception as e:
            err_msg = f"Unexpected error during Gitleaks scan: {e}"
            logger.error(f"[Gitleaks] {err_msg}")
            return ScannerResult(
                scanner_name="gitleaks",
                executed=True,
                status="FAILED",
                error_message=err_msg[:1024],
                findings=[],
            )
        finally:
            if os.path.exists(report_path):
                try:
                    os.remove(report_path)
                except OSError:
                    pass
