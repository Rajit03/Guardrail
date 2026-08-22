import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.scan import Scan
from app.models.finding import Finding
from app.models.repository import Repository
from app.services.repository_acquisition import acquire_repository
from app.services.risk_service import RiskService
from app.scanners.runner import ScannerRunner

logger = logging.getLogger(__name__)


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
        # 1. Create Scan record with RUNNING status
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
            # 2. Acquire repository securely via zip download
            with acquire_repository(repository) as repo_path:
                # 3. Run all scanners
                finding_data_list = runner.run_all(repo_path)

                # 4. Normalize and store each finding & calculate risk assessment
                created_findings = []
                for f_data in finding_data_list:
                    fingerprint_str = (
                        f"{repository.id}-{f_data.scanner}-{f_data.rule_id}"
                        f"-{f_data.file_path}-{f_data.line_number}-{f_data.type}"
                    )
                    fingerprint = hashlib.sha256(fingerprint_str.encode()).hexdigest()

                    finding = Finding(
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
                        fingerprint=fingerprint
                    )
                    db.add(finding)
                    created_findings.append(finding)

                db.commit()

                # Automatically calculate risk assessments for new findings
                for f in created_findings:
                    db.refresh(f)
                    RiskService.compute_and_save_risk_assessment(db, f, repository)

                scan.total_findings = len(finding_data_list)
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
