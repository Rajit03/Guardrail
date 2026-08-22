import logging
from typing import List
from app.scanners.base import BaseScanner, FindingData
from app.scanners.secrets.gitleaks import GitleaksScanner
from app.scanners.dependencies.osv import OSVScanner

logger = logging.getLogger(__name__)


class ScannerRunner:
    """
    Runner for executing registered security scanners on a local repository.
    Aggregates findings and ensures isolated failure handling for each scanner.
    """

    def __init__(self):
        self.scanners: List[BaseScanner] = [
            GitleaksScanner(),
            OSVScanner()
        ]

    def run_all(self, repository_path: str) -> List[FindingData]:
        all_findings: List[FindingData] = []
        for scanner in self.scanners:
            scanner_name = scanner.__class__.__name__
            try:
                logger.info(f"Running scanner: {scanner_name}")
                findings = scanner.scan(repository_path)
                logger.info(f"Scanner {scanner_name} completed with {len(findings)} findings.")
                all_findings.extend(findings)
            except Exception as e:
                logger.error(f"Scanner {scanner_name} failed: {e}", exc_info=True)
                # Continue with remaining scanners instead of crashing the scan job
                continue
        return all_findings
