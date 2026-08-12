import logging
from typing import List
from .base import BaseScanner, FindingData
from .secrets.gitleaks import GitleaksScanner
from .dependencies.osv import OSVScanner

logger = logging.getLogger(__name__)

class ScannerRunner:
    def __init__(self):
        self.scanners: List[BaseScanner] = [
            GitleaksScanner(),
            OSVScanner()
        ]
        
    def run_all(self, repository_path: str) -> List[FindingData]:
        all_findings = []
        for scanner in self.scanners:
            try:
                findings = scanner.scan(repository_path)
                all_findings.extend(findings)
            except Exception as e:
                logger.error(f"Scanner {scanner.__class__.__name__} failed: {e}", exc_info=True)
                # Continue with other scanners instead of failing the whole scan
                continue
        return all_findings
