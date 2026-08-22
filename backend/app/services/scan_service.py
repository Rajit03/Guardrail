import os
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.scan import Scan
from app.models.finding import Finding
from app.models.repository import Repository
from app.services.repository_acquisition import acquire_repository
from app.services.risk_service import RiskService
from app.scanners.runner import ScannerRunner

logger = logging.getLogger(__name__)


def inspect_repository_files(repo_path: str) -> Tuple[int, List[str], List[str], bool]:
    """
    Recursively inspects repository path to produce file counts and manifest lists.
    Returns: (total_files_count, dependency_files, python_files, dot_env_exists)
    """
    total_files = 0
    dependency_files = []
    python_files = []
    dot_env_exists = False

    known_manifests = {
        "requirements.txt", "pyproject.toml", "poetry.lock", "pipfile", "pipfile.lock",
        "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"
    }

    for root, dirs, files in os.walk(repo_path):
        if ".git" in dirs:
            dirs.remove(".git")

        for filename in files:
            total_files += 1
            full_p = os.path.join(root, filename)
            rel_p = os.path.relpath(full_p, repo_path).replace("\\", "/")

            if filename.lower() == ".env" or filename.lower().startswith(".env."):
                dot_env_exists = True

            if filename.lower() in known_manifests or (filename.endswith(".txt") and "requirements" in root.lower()):
                dependency_files.append(rel_p)

            if filename.endswith(".py"):
                python_files.append(rel_p)

    return total_files, dependency_files, python_files, dot_env_exists


class ScanService:
    @staticmethod
    def get_scan(db: Session, scan_id: uuid.UUID | str) -> Optional[Scan]:
        if isinstance(scan_id, str):
            try:
                scan_id = uuid.UUID(scan_id)
            except ValueError:
                return None
        return db.scalar(select(Scan).where(Scan.id == scan_id))

    @staticmethod
    def get_scans_for_repository(db: Session, repository_id: uuid.UUID | str) -> List[Scan]:
        if isinstance(repository_id, str):
            try:
                repository_id = uuid.UUID(repository_id)
            except ValueError:
                return []
        return list(db.scalars(
            select(Scan)
            .where(Scan.repository_id == repository_id)
            .order_by(Scan.created_at.desc())
        ).all())

    @staticmethod
    def run_scan(db: Session, repository: Repository) -> Scan:
        now_utc = datetime.now(timezone.utc)
        scan = Scan(
            repository_id=repository.id,
            status="RUNNING",
            started_at=now_utc
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        runner = ScannerRunner()

        try:
            with acquire_repository(repository) as repo_path:
                # 1. Inspect repository contents & log diagnostic context
                total_files, dep_files, py_files, env_exists = inspect_repository_files(repo_path)
                logger.info(
                    f"Acquired Repository Path: '{repo_path}' | Total Files: {total_files} | "
                    f".env present: {env_exists} | Manifests: {dep_files}"
                )

                # 2. Execute security scanners
                finding_data_list, scanner_results = runner.run_all(repo_path)

                # 3. Deduplicate & Upsert Findings in PostgreSQL
                active_findings: List[Finding] = []
                seen_fingerprints_in_scan = set()

                for f_data in finding_data_list:
                    # Deterministic fingerprint generation
                    if f_data.type == "DEPENDENCY":
                        fingerprint_raw = (
                            f"{repository.id}-osv-{f_data.package_name or ''}-"
                            f"{f_data.installed_version or ''}-{f_data.vulnerability_id or f_data.rule_id or ''}-"
                            f"{f_data.file_path or ''}"
                        )
                    else:
                        fingerprint_raw = (
                            f"{repository.id}-gitleaks-{f_data.rule_id or ''}-"
                            f"{f_data.file_path or ''}-{f_data.line_number or 0}"
                        )
                    fingerprint = hashlib.sha256(fingerprint_raw.encode("utf-8")).hexdigest()

                    # Deduplicate within same scan execution
                    if fingerprint in seen_fingerprints_in_scan:
                        continue
                    seen_fingerprints_in_scan.add(fingerprint)

                    # Lookup existing finding in database by repository_id and fingerprint
                    existing_finding = db.scalar(
                        select(Finding).where(
                            Finding.repository_id == repository.id,
                            Finding.fingerprint == fingerprint
                        )
                    )

                    if existing_finding:
                        existing_finding.scan_id = scan.id
                        existing_finding.severity = f_data.severity
                        existing_finding.title = f_data.title
                        existing_finding.description = f_data.description
                        existing_finding.evidence = f_data.evidence
                        existing_finding.recommendation = f_data.recommendation
                        existing_finding.package_name = f_data.package_name
                        existing_finding.installed_version = f_data.installed_version
                        existing_finding.fixed_version = f_data.fixed_version
                        existing_finding.vulnerability_id = f_data.vulnerability_id
                        existing_finding.aliases = f_data.aliases
                        existing_finding.updated_at = datetime.now(timezone.utc)
                        active_findings.append(existing_finding)
                    else:
                        new_finding = Finding(
                            repository_id=repository.id,
                            scan_id=scan.id,
                            type=f_data.type,
                            severity=f_data.severity,
                            title=f_data.title,
                            description=f_data.description,
                            file_path=f_data.file_path,
                            line_number=f_data.line_number,
                            scanner=f_data.scanner,
                            rule_id=f_data.rule_id,
                            evidence=f_data.evidence,
                            recommendation=f_data.recommendation,
                            status="OPEN",
                            fingerprint=fingerprint,
                            package_name=f_data.package_name,
                            installed_version=f_data.installed_version,
                            fixed_version=f_data.fixed_version,
                            vulnerability_id=f_data.vulnerability_id,
                            aliases=f_data.aliases,
                        )
                        db.add(new_finding)
                        active_findings.append(new_finding)

                db.commit()

                # 4. Compute risk assessments for active findings
                for f in active_findings:
                    db.refresh(f)
                    RiskService.compute_and_save_risk_assessment(db, f, repository)

                # 5. Populate scan summary & status
                gitleaks_res = scanner_results.get("gitleaks")
                osv_res = scanner_results.get("osv")

                gitleaks_status = gitleaks_res.status if gitleaks_res else "SKIPPED"
                osv_status = osv_res.status if osv_res else "SKIPPED"

                scan.total_findings = len(active_findings)
                scan.scan_summary = {
                    "files_scanned": total_files,
                    "dependency_files": dep_files,
                    "python_files": py_files,
                    "dot_env_exists": env_exists,
                    "secret_scanner_status": gitleaks_status,
                    "dependency_scanner_status": osv_status,
                    "scanners": {
                        "gitleaks": {
                            "executed": gitleaks_res.executed if gitleaks_res else False,
                            "status": gitleaks_status,
                            "raw_findings": gitleaks_res.raw_findings_count if gitleaks_res else 0,
                            "normalized_findings": gitleaks_res.normalized_findings_count if gitleaks_res else 0,
                            "error_message": gitleaks_res.error_message if gitleaks_res else None,
                        },
                        "osv": {
                            "executed": osv_res.executed if osv_res else False,
                            "status": osv_status,
                            "raw_vulnerabilities": osv_res.raw_findings_count if osv_res else 0,
                            "normalized_findings": osv_res.normalized_findings_count if osv_res else 0,
                            "deduplicated_findings": osv_res.deduplicated_findings_count if osv_res else 0,
                            "error_message": osv_res.error_message if osv_res else None,
                        }
                    },
                    "total_findings": len(active_findings)
                }

                # Determine overall scan status: FAILED if all scanners failed, otherwise COMPLETED
                if gitleaks_status == "FAILED" and osv_status == "FAILED":
                    scan.status = "FAILED"
                    scan.error_message = "All security scanners failed to execute."
                else:
                    scan.status = "COMPLETED"

        except Exception as e:
            logger.error(f"Scan {scan.id} failed: {e}", exc_info=True)
            scan.status = "FAILED"
            scan.error_message = str(e)[:1024]

        finally:
            finished_at = datetime.now(timezone.utc)
            scan.completed_at = finished_at
            repository.last_scan_at = finished_at
            db.commit()
            db.refresh(scan)

        return scan
