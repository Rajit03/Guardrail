from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FindingData:
    type: str  # "SECRET", "DEPENDENCY"
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"
    title: str
    scanner: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    rule_id: Optional[str] = None
    evidence: Optional[str] = None
    recommendation: Optional[str] = None

    # Expanded Dependency & Vulnerability Fields
    package_name: Optional[str] = None
    installed_version: Optional[str] = None
    fixed_version: Optional[str] = None
    vulnerability_id: Optional[str] = None
    aliases: Optional[List[str]] = field(default_factory=list)


@dataclass
class ScannerResult:
    scanner_name: str
    executed: bool
    status: str  # "COMPLETED", "FAILED", "SKIPPED"
    error_message: Optional[str] = None
    raw_findings_count: int = 0
    normalized_findings_count: int = 0
    deduplicated_findings_count: int = 0
    findings: List[FindingData] = field(default_factory=list)


class BaseScanner:
    def scan(self, repository_path: str) -> ScannerResult:
        """
        Scan a local repository and return a ScannerResult containing status and findings.
        Must be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement the scan method.")
