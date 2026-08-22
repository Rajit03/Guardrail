import logging
from typing import List, Dict, Tuple
from app.scanners.base import BaseScanner, FindingData, ScannerResult
from app.scanners.secrets.gitleaks import GitleaksScanner
from app.scanners.dependencies.osv import OSVScanner

logger = logging.getLogger(__name__)


class ScannerRunner:
    """
    Runner for executing registered security scanners on a local repository.
    Aggregates findings and ensures isolated failure handling and status reporting.
    """

    def __init__(self):
        self.scanners: List[BaseScanner] = [
            GitleaksScanner(),
            OSVScanner()
        ]

    def run_all(self, repository_path: str) -> Tuple[List[FindingData], Dict[str, ScannerResult]]:
        all_findings: List[FindingData] = []
        scanner_results: Dict[str, ScannerResult] = {}

        for scanner in self.scanners:
            scanner_class_name = scanner.__class__.__name__
            try:
                logger.info(f"Running scanner: {scanner_class_name}")
                result: ScannerResult = scanner.scan(repository_path)
                logger.info(
                    f"Scanner {result.scanner_name} completed with status '{result.status}' "
                    f"({len(result.findings)} findings)."
                )
                scanner_results[result.scanner_name] = result
                all_findings.extend(result.findings)
            except Exception as e:
                logger.error(f"Scanner {scanner_class_name} threw an exception: {e}", exc_info=True)
                failed_res = ScannerResult(
                    scanner_name=scanner_class_name.lower().replace("scanner", ""),
                    executed=True,
                    status="FAILED",
                    error_message=str(e)[:1024],
                    findings=[]
                )
                scanner_results[failed_res.scanner_name] = failed_res

        return all_findings, scanner_results
