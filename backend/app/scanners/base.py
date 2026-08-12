from dataclasses import dataclass
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


class BaseScanner:
    def scan(self, repository_path: str) -> List[FindingData]:
        """
        Scan a local repository and return a list of findings.
        This must be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement the scan method.")
